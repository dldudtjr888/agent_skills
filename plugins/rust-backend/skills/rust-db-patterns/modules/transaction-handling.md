# Transaction Handling

트랜잭션 패턴, 중첩 트랜잭션, 에러 롤백 전략.

## SQLx 트랜잭션

### 기본 트랜잭션

```rust
pub async fn transfer_funds(
    pool: &PgPool,
    from_id: i64,
    to_id: i64,
    amount: Decimal,
) -> Result<(), Error> {
    let mut tx = pool.begin().await?;

    // 출금
    sqlx::query!(
        "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
        amount,
        from_id
    )
    .execute(&mut *tx)
    .await?;

    // 입금
    sqlx::query!(
        "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
        amount,
        to_id
    )
    .execute(&mut *tx)
    .await?;

    // 커밋
    tx.commit().await?;

    Ok(())
}
```

### 자동 롤백

```rust
pub async fn create_user_with_profile(
    pool: &PgPool,
    user: NewUser,
    profile: NewProfile,
) -> Result<User, Error> {
    let mut tx = pool.begin().await?;

    // tx가 drop되면 자동 롤백
    let user = sqlx::query_as!(
        User,
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *",
        user.name,
        user.email
    )
    .fetch_one(&mut *tx)
    .await?;

    sqlx::query!(
        "INSERT INTO profiles (user_id, bio) VALUES ($1, $2)",
        user.id,
        profile.bio
    )
    .execute(&mut *tx)
    .await?;

    tx.commit().await?;

    Ok(user)
}
```

### Savepoint (중첩 트랜잭션)

```rust
pub async fn complex_operation(pool: &PgPool) -> Result<(), Error> {
    let mut tx = pool.begin().await?;

    // 메인 작업
    sqlx::query!("INSERT INTO logs (message) VALUES ('started')")
        .execute(&mut *tx)
        .await?;

    // 중첩 트랜잭션 (savepoint)
    let savepoint = tx.begin().await?;

    match risky_operation(&mut *savepoint).await {
        Ok(_) => {
            savepoint.commit().await?;
        }
        Err(e) => {
            // savepoint만 롤백, 메인 tx는 유지
            tracing::warn!("Risky operation failed: {}", e);
            savepoint.rollback().await?;
        }
    }

    // 메인 작업 계속
    sqlx::query!("INSERT INTO logs (message) VALUES ('completed')")
        .execute(&mut *tx)
        .await?;

    tx.commit().await?;
    Ok(())
}
```

## Diesel 트랜잭션

### 기본 트랜잭션

```rust
use diesel::Connection;

pub fn transfer_funds(
    conn: &mut PgConnection,
    from_id: i32,
    to_id: i32,
    amount: BigDecimal,
) -> QueryResult<()> {
    conn.transaction(|conn| {
        diesel::update(accounts::table.find(from_id))
            .set(accounts::balance.eq(accounts::balance - &amount))
            .execute(conn)?;

        diesel::update(accounts::table.find(to_id))
            .set(accounts::balance.eq(accounts::balance + &amount))
            .execute(conn)?;

        Ok(())
    })
}
```

### 중첩 트랜잭션

```rust
pub fn nested_transaction(conn: &mut PgConnection) -> QueryResult<()> {
    conn.transaction(|conn| {
        // 외부 트랜잭션 작업
        diesel::insert_into(logs::table)
            .values(logs::message.eq("outer"))
            .execute(conn)?;

        // 내부 트랜잭션 (savepoint)
        let result = conn.transaction(|conn| {
            diesel::insert_into(logs::table)
                .values(logs::message.eq("inner"))
                .execute(conn)?;

            // 의도적 실패
            Err::<(), _>(diesel::result::Error::RollbackTransaction)
        });

        // 내부 실패해도 외부는 계속
        if result.is_err() {
            tracing::warn!("Inner transaction rolled back");
        }

        Ok(())
    })
}
```

## SeaORM 트랜잭션

```rust
use sea_orm::{TransactionTrait, DatabaseTransaction};

pub async fn create_order(
    db: &DatabaseConnection,
    order: NewOrder,
    items: Vec<NewOrderItem>,
) -> Result<order::Model, DbErr> {
    db.transaction::<_, order::Model, DbErr>(|txn| {
        Box::pin(async move {
            let order = order::ActiveModel {
                user_id: Set(order.user_id),
                total: Set(order.total),
                ..Default::default()
            };

            let order = order.insert(txn).await?;

            for item in items {
                let order_item = order_item::ActiveModel {
                    order_id: Set(order.id),
                    product_id: Set(item.product_id),
                    quantity: Set(item.quantity),
                    ..Default::default()
                };
                order_item.insert(txn).await?;
            }

            Ok(order)
        })
    })
    .await
}
```

## 고급 패턴

### 낙관적 락 (Optimistic Locking)

```rust
pub async fn update_with_version(
    pool: &PgPool,
    id: i64,
    new_value: &str,
    expected_version: i32,
) -> Result<bool, Error> {
    let result = sqlx::query!(
        r#"
        UPDATE items
        SET value = $1, version = version + 1
        WHERE id = $2 AND version = $3
        "#,
        new_value,
        id,
        expected_version
    )
    .execute(pool)
    .await?;

    Ok(result.rows_affected() > 0)
}

// 재시도 로직
pub async fn update_with_retry(
    pool: &PgPool,
    id: i64,
    update_fn: impl Fn(&Item) -> String,
) -> Result<Item, Error> {
    for _ in 0..3 {
        let item = get_item(pool, id).await?;
        let new_value = update_fn(&item);

        if update_with_version(pool, id, &new_value, item.version).await? {
            return get_item(pool, id).await;
        }

        tokio::time::sleep(Duration::from_millis(100)).await;
    }

    Err(Error::ConcurrentModification)
}
```

### 비관적 락 (Pessimistic Locking)

```rust
pub async fn process_with_lock(
    pool: &PgPool,
    id: i64,
) -> Result<(), Error> {
    let mut tx = pool.begin().await?;

    // FOR UPDATE로 행 잠금
    let item = sqlx::query_as!(
        Item,
        "SELECT * FROM items WHERE id = $1 FOR UPDATE",
        id
    )
    .fetch_one(&mut *tx)
    .await?;

    // 안전하게 처리
    let new_value = expensive_computation(&item);

    sqlx::query!(
        "UPDATE items SET value = $1 WHERE id = $2",
        new_value,
        id
    )
    .execute(&mut *tx)
    .await?;

    tx.commit().await?;
    Ok(())
}
```

### 분산 트랜잭션 패턴 (Saga)

```rust
pub async fn create_order_saga(
    pool: &PgPool,
    order: NewOrder,
) -> Result<Order, Error> {
    // 1. 주문 생성
    let order = create_order(pool, &order).await?;

    // 2. 재고 차감
    if let Err(e) = decrease_inventory(pool, &order).await {
        // 보상 트랜잭션: 주문 취소
        cancel_order(pool, order.id).await?;
        return Err(e);
    }

    // 3. 결제 처리
    if let Err(e) = process_payment(pool, &order).await {
        // 보상 트랜잭션: 재고 복구, 주문 취소
        restore_inventory(pool, &order).await?;
        cancel_order(pool, order.id).await?;
        return Err(e);
    }

    Ok(order)
}
```

## 격리 수준

```rust
// SQLx에서 격리 수준 설정
pub async fn read_committed_tx(pool: &PgPool) -> Result<(), Error> {
    let mut tx = pool.begin().await?;

    sqlx::query("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
        .execute(&mut *tx)
        .await?;

    // 작업 수행...

    tx.commit().await?;
    Ok(())
}

// PostgreSQL 격리 수준
// - READ UNCOMMITTED (PostgreSQL에서는 READ COMMITTED로 처리)
// - READ COMMITTED (기본값)
// - REPEATABLE READ
// - SERIALIZABLE
```

## 체크리스트

- [ ] 트랜잭션 범위 최소화
- [ ] 자동 롤백 활용 (drop 시)
- [ ] 중첩 트랜잭션에 savepoint 사용
- [ ] 동시성 제어 전략 선택 (낙관적/비관적)
- [ ] 데드락 방지 (일관된 락 순서)
- [ ] 적절한 격리 수준 설정
- [ ] 장기 실행 트랜잭션 회피
- [ ] 보상 트랜잭션 구현 (분산 시스템)
