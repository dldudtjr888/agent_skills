# Python Refactoring Patterns

Comprehensive guide to Python-specific refactoring patterns, organized by Martin Fowler's refactoring catalog with Python-specific implementations.

## Table of Contents

1. [Basic Refactorings](#basic-refactorings)
2. [Organizing Data](#organizing-data)
3. [Simplifying Conditional Logic](#simplifying-conditional-logic)
4. [Moving Features](#moving-features)
5. [Dealing with Inheritance](#dealing-with-inheritance)
6. [Python-Specific Patterns](#python-specific-patterns)

---

## Basic Refactorings

### Extract Function/Method

**When to Use**: Function > 50 lines, complex logic, repeated code blocks

**Using Rope Library**:
```python
from rope.base.project import Project
from rope.refactor.extract import ExtractMethod

proj = Project('.')
resource = proj.get_file('mymodule.py')

# Extract lines 45-78 into new method
extractor = ExtractMethod(proj, resource, start_offset=1200, end_offset=2400)
changes = extractor.get_changes('extracted_method', similar=True, global_=False)
proj.do(changes)
```

**Manual Example**:
```python
# Before
def process_order(order):
    # Validate order
    if not order.items:
        raise ValueError("Order must have items")
    if order.total < 0:
        raise ValueError("Invalid total")
    
    # Calculate discounts
    discount = 0
    if order.customer.is_premium:
        discount = order.total * 0.10
    if order.total > 1000:
        discount += 50
    
    # Process payment
    payment_result = payment_gateway.charge(
        order.customer.payment_method,
        order.total - discount
    )
    
    # Send notifications
    email.send_confirmation(order.customer.email, order.id)
    sms.send_confirmation(order.customer.phone, order.id)
    
    return payment_result

# After - Extracted methods
def process_order(order):
    validate_order(order)
    discount = calculate_discount(order)
    payment_result = process_payment(order, discount)
    send_notifications(order)
    return payment_result

def validate_order(order):
    if not order.items:
        raise ValueError("Order must have items")
    if order.total < 0:
        raise ValueError("Invalid total")

def calculate_discount(order):
    discount = 0
    if order.customer.is_premium:
        discount = order.total * 0.10
    if order.total > 1000:
        discount += 50
    return discount

def process_payment(order, discount):
    return payment_gateway.charge(
        order.customer.payment_method,
        order.total - discount
    )

def send_notifications(order):
    email.send_confirmation(order.customer.email, order.id)
    sms.send_confirmation(order.customer.phone, order.id)
```

### Inline Function

**When to Use**: Function body is as clear as its name, over-abstraction

**Using Rope**:
```python
from rope.refactor.inline import InlineMethod

inliner = InlineMethod(proj, resource, offset=500)
changes = inliner.get_changes()
proj.do(changes)
```

**Manual Example**:
```python
# Before
def get_rating(driver):
    return more_than_five_late_deliveries(driver) ? 2 : 1

def more_than_five_late_deliveries(driver):
    return driver.late_deliveries > 5

# After - Inline the simple check
def get_rating(driver):
    return 2 if driver.late_deliveries > 5 else 1
```

### Extract Variable

**When to Use**: Complex expressions, repeated calculations

```python
# Before
def price_with_discount(order):
    return order.quantity * order.item_price - \
           max(0, order.quantity - 500) * order.item_price * 0.05 + \
           min(order.quantity * order.item_price * 0.1, 100)

# After
def price_with_discount(order):
    base_price = order.quantity * order.item_price
    quantity_discount = max(0, order.quantity - 500) * order.item_price * 0.05
    shipping = min(base_price * 0.1, 100)
    return base_price - quantity_discount + shipping
```

### Rename Variable/Function/Class

**Using Rope**:
```python
from rope.refactor.rename import Rename

rename = Rename(proj, resource, offset=300)
changes = rename.get_changes('new_name')
proj.do(changes)
```

**Best Practices**:
- Use descriptive names: `customer_orders` not `co`
- Boolean variables: `is_active`, `has_permission`
- Functions: Verb + noun: `calculate_total`, `validate_input`
- Classes: Noun: `OrderProcessor`, `UserValidator`

---

## Organizing Data

### Replace Primitive with Object

**When to Use**: Primitive has associated behavior or validation

```python
# Before
class Order:
    def __init__(self, weight_kg: float, distance_km: int):
        self.weight_kg = weight_kg
        self.distance_km = distance_km
    
    def calculate_shipping(self) -> float:
        return self.weight_kg * 2.5 + self.distance_km * 0.5

# After
class Weight:
    def __init__(self, kilograms: float):
        if kilograms < 0:
            raise ValueError("Weight cannot be negative")
        self._kg = kilograms
    
    @property
    def kilograms(self) -> float:
        return self._kg
    
    @property
    def pounds(self) -> float:
        return self._kg * 2.20462
    
    def __repr__(self):
        return f"Weight({self._kg}kg)"

class Distance:
    def __init__(self, kilometers: int):
        if kilometers < 0:
            raise ValueError("Distance cannot be negative")
        self._km = kilometers
    
    @property
    def kilometers(self) -> int:
        return self._km
    
    @property
    def miles(self) -> float:
        return self._km * 0.621371

class Order:
    def __init__(self, weight: Weight, distance: Distance):
        self.weight = weight
        self.distance = distance
    
    def calculate_shipping(self) -> float:
        return self.weight.kilograms * 2.5 + self.distance.kilometers * 0.5
```

### Encapsulate Collection

**When to Use**: Exposing mutable collections directly

```python
# Before
class Course:
    def __init__(self):
        self.students = []  # Direct access allows external modification

course = Course()
course.students.append(student)  # Breaks encapsulation
course.students.clear()  # Can accidentally clear all students

# After
class Course:
    def __init__(self):
        self._students = []
    
    def add_student(self, student):
        if student not in self._students:
            self._students.append(student)
    
    def remove_student(self, student):
        if student in self._students:
            self._students.remove(student)
    
    def get_students(self):
        return list(self._students)  # Return copy
    
    @property
    def student_count(self):
        return len(self._students)
```

### Replace Type Code with Class

**When to Use**: Using strings/ints for types

```python
# Before
class Employee:
    ENGINEER = 0
    SALESMAN = 1
    MANAGER = 2
    
    def __init__(self, name, type_code):
        self.name = name
        self.type = type_code

# After - Using Enum
from enum import Enum, auto

class EmployeeType(Enum):
    ENGINEER = auto()
    SALESMAN = auto()
    MANAGER = auto()

class Employee:
    def __init__(self, name, employee_type: EmployeeType):
        self.name = name
        self.type = employee_type

# Even Better - Using classes (Strategy pattern)
class Employee:
    def __init__(self, name, employee_type):
        self.name = name
        self._type = employee_type
    
    def get_bonus(self):
        return self._type.calculate_bonus(self)

class EngineerType:
    def calculate_bonus(self, employee):
        return employee.base_salary * 0.10

class SalesmanType:
    def calculate_bonus(self, employee):
        return employee.sales * 0.05

class ManagerType:
    def calculate_bonus(self, employee):
        return employee.base_salary * 0.15
```

---

## Simplifying Conditional Logic

### Decompose Conditional

**When to Use**: Complex if statements, nested conditions

```python
# Before
if date.before(SUMMER_START) or date.after(SUMMER_END):
    charge = quantity * winter_rate + winter_service_charge
else:
    charge = quantity * summer_rate

# After
def is_summer(date):
    return not (date.before(SUMMER_START) or date.after(SUMMER_END))

def calculate_winter_charge(quantity):
    return quantity * winter_rate + winter_service_charge

def calculate_summer_charge(quantity):
    return quantity * summer_rate

charge = calculate_summer_charge(quantity) if is_summer(date) \
         else calculate_winter_charge(quantity)
```

### Replace Nested Conditional with Guard Clauses

**When to Use**: Nested if statements > 3 levels

```python
# Before
def get_payment_amount(employee):
    result = 0
    if employee.is_separated:
        result = calculate_separated_amount(employee)
    else:
        if employee.is_retired:
            result = calculate_retired_amount(employee)
        else:
            if employee.is_part_time:
                result = calculate_part_time_amount(employee)
            else:
                result = calculate_normal_amount(employee)
    return result

# After - Guard clauses
def get_payment_amount(employee):
    if employee.is_separated:
        return calculate_separated_amount(employee)
    
    if employee.is_retired:
        return calculate_retired_amount(employee)
    
    if employee.is_part_time:
        return calculate_part_time_amount(employee)
    
    return calculate_normal_amount(employee)
```

### Replace Conditional with Polymorphism

**When to Use**: Type-based conditionals, switch statements

```python
# Before
class Bird:
    def __init__(self, bird_type):
        self.type = bird_type
    
    def get_speed(self):
        if self.type == "EUROPEAN":
            return self.get_base_speed()
        elif self.type == "AFRICAN":
            return self.get_base_speed() - self.get_load_factor()
        elif self.type == "NORWEGIAN_BLUE":
            return 0 if self.is_nailed else self.get_base_speed()

# After - Polymorphism
from abc import ABC, abstractmethod

class Bird(ABC):
    @abstractmethod
    def get_speed(self):
        pass
    
    def get_base_speed(self):
        return 10

class EuropeanBird(Bird):
    def get_speed(self):
        return self.get_base_speed()

class AfricanBird(Bird):
    def __init__(self, load_factor):
        self.load_factor = load_factor
    
    def get_speed(self):
        return self.get_base_speed() - self.load_factor

class NorwegianBlueBird(Bird):
    def __init__(self, is_nailed):
        self.is_nailed = is_nailed
    
    def get_speed(self):
        return 0 if self.is_nailed else self.get_base_speed()
```

---

## Moving Features

### Move Function

**When to Use**: Function uses more features of another class

**Using Rope**:
```python
from rope.refactor.move import MoveMethod

mover = MoveMethod(proj, resource, offset=500)
changes = mover.get_changes(dest_attr='target_class')
proj.do(changes)
```

### Move Field

**When to Use**: Field is used more by another class

```python
# Before
class Account:
    def __init__(self):
        self.interest_rate = 0.05

class AccountType:
    def calculate_interest(self, account, days):
        return account.balance * account.interest_rate * days / 365

# After
class AccountType:
    def __init__(self):
        self.interest_rate = 0.05
    
    def calculate_interest(self, account, days):
        return account.balance * self.interest_rate * days / 365

class Account:
    def __init__(self, account_type):
        self.account_type = account_type
```

### Extract Class

**When to Use**: Class has too many responsibilities

```python
# Before
class Person:
    def __init__(self, name, office_phone, office_ext):
        self.name = name
        self.office_phone = office_phone
        self.office_extension = office_ext
    
    def get_telephone_number(self):
        return f"{self.office_phone} x{self.office_extension}"

# After
class TelephoneNumber:
    def __init__(self, phone, extension):
        self.phone = phone
        self.extension = extension
    
    def __str__(self):
        return f"{self.phone} x{self.extension}"

class Person:
    def __init__(self, name, phone, extension):
        self.name = name
        self.office_phone = TelephoneNumber(phone, extension)
    
    def get_telephone_number(self):
        return str(self.office_phone)
```

---

## Python-Specific Patterns

### Use Dataclasses for Value Objects

```python
# Before
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __repr__(self):
        return f"Point({self.x}, {self.y})"

# After
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: float
    y: float
```

### Use Type Hints

```python
# Before
def calculate_total(items):
    return sum(item.price * item.quantity for item in items)

# After
from typing import List, Protocol

class Item(Protocol):
    price: float
    quantity: int

def calculate_total(items: List[Item]) -> float:
    return sum(item.price * item.quantity for item in items)
```

### Use Context Managers

```python
# Before
file = open('data.txt', 'r')
try:
    data = file.read()
    process(data)
finally:
    file.close()

# After
with open('data.txt', 'r') as file:
    data = file.read()
    process(data)

# Custom context manager
from contextlib import contextmanager

@contextmanager
def transaction(db):
    db.begin()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

# Usage
with transaction(db) as tx:
    tx.execute("INSERT ...")
```

### Use List/Dict Comprehensions

```python
# Before
result = []
for item in items:
    if item.is_valid():
        result.append(item.name.upper())

# After
result = [item.name.upper() for item in items if item.is_valid()]

# Dict comprehension
# Before
result = {}
for key, value in data.items():
    if value > 0:
        result[key] = value * 2

# After
result = {key: value * 2 for key, value in data.items() if value > 0}
```

### Use Generators for Large Datasets

```python
# Before - Loads everything into memory
def get_all_records():
    records = []
    for record in database.query():
        if record.is_valid():
            records.append(process(record))
    return records

# After - Generator
def get_all_records():
    for record in database.query():
        if record.is_valid():
            yield process(record)

# Usage
for record in get_all_records():
    # Process one at a time
    handle(record)
```

### Use Decorators for Cross-Cutting Concerns

```python
from functools import wraps
import time

# Logging decorator
def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}")
        return result
    return wrapper

# Timing decorator
def timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper

# Usage
@log_calls
@timing
def expensive_operation(data):
    # ... processing
    return result
```

---

## Rope Library Reference

### Common Rope Operations

```python
from rope.base.project import Project
from rope.refactor.rename import Rename
from rope.refactor.extract import ExtractMethod, ExtractVariable
from rope.refactor.inline import InlineMethod
from rope.refactor.move import MoveMethod, MoveModule
from rope.refactor.restructure import Restructure
from rope.refactor.change_signature import ChangeSignature

# Initialize project
proj = Project('.')

# Get resource (file)
resource = proj.get_file('mymodule.py')

# Or by path
from rope.base import libutils
resource = libutils.path_to_resource(proj, '/path/to/file.py')

# Rename
renamer = Rename(proj, resource, offset=100)
changes = renamer.get_changes('new_name')
proj.do(changes)

# Extract method
extractor = ExtractMethod(proj, resource, start=100, end=200)
changes = extractor.get_changes('extracted_method_name')
proj.do(changes)

# Move method
mover = MoveMethod(proj, resource, offset=100)
changes = mover.get_changes(dest='destination_attribute')
proj.do(changes)

# Change signature
changer = ChangeSignature(proj, resource, offset=100)
changes = changer.get_changes([
    {'name': 'new_param', 'default': 'None'}
])
proj.do(changes)
```

### Safety with Rope

```python
# Always work with clean git state
import subprocess

def ensure_clean_state():
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    if result.stdout.strip():
        raise RuntimeError("Git working directory is not clean")

# Dry-run mode
changes = refactoring.get_changes()
print(changes.get_description())  # Preview changes

# Only apply if approved
if user_approves():
    proj.do(changes)
```
