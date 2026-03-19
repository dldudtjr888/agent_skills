# Ownership and Borrowing Patterns

## Prefer Slices and References in Parameters

```rust
// Good: Accept slices for maximum flexibility
fn sum(values: &[i32]) -> i32 {
    values.iter().sum()
}

fn contains_keyword(text: &str, keyword: &str) -> bool {
    text.contains(keyword)
}

// Bad: Require owned types unnecessarily
fn sum(values: Vec<i32>) -> i32 {
    values.iter().sum()
}
```

## Avoid Unnecessary .clone()

```rust
// Good: Restructure to use references
fn process(data: &Data) -> Result<Output, Error> {
    let result = compute(&data.field)?;
    Ok(Output { result })
}

// Bad: Clone to satisfy the borrow checker — redesign instead
fn process(data: &Data) -> Result<Output, Error> {
    let owned = data.field.clone(); // Unnecessary heap allocation
    let result = compute(&owned)?;
    Ok(Output { result })
}
```

## Cow for Conditional Ownership

```rust
use std::borrow::Cow;

// Good: Zero-cost borrow when no modification needed
fn normalize(input: &str) -> Cow<'_, str> {
    if input.contains(' ') {
        Cow::Owned(input.replace(' ', "_"))
    } else {
        Cow::Borrowed(input) // No allocation
    }
}

// Usage: Deref handles both variants transparently
let result = normalize("hello world");
println!("{result}"); // Works for both Borrowed and Owned

// Bad: Always allocates even when the input is already valid
fn normalize(input: &str) -> String {
    if input.contains(' ') {
        input.replace(' ', "_")
    } else {
        input.to_owned() // Unnecessary heap allocation
    }
}
```
