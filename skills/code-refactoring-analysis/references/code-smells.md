# Code Smells Detection Guide

Comprehensive catalog of code smells with detection criteria and refactoring recommendations.

## Bloaters

Code smells that have grown to excessive proportions.

### Long Method
- **Detection**: Function/method > 50 lines
- **Signs**: Scrolling required, multiple responsibilities
- **Refactoring**: Extract Method, Replace Temp with Query
- **Python Example**: Function with 150+ lines
- **JavaScript Example**: Component with 200+ lines

### Large Class
- **Detection**: Class > 300 lines or > 10 methods
- **Signs**: Too many instance variables, duplicated code
- **Refactoring**: Extract Class, Extract Subclass
- **Threshold**: > 500 LOC critical

### Primitive Obsession
- **Detection**: Using primitives instead of small objects
- **Signs**: Phone numbers as strings, money as floats
- **Refactoring**: Replace Primitive with Object, Replace Type Code with Class

### Long Parameter List
- **Detection**: > 5 parameters
- **Signs**: Difficult to understand, changes frequently
- **Refactoring**: Introduce Parameter Object, Preserve Whole Object

### Data Clumps
- **Detection**: Same group of data items together in multiple places
- **Signs**: Same 3+ fields in multiple classes
- **Refactoring**: Extract Class, Introduce Parameter Object

## Object-Orientation Abusers

### Switch Statements
- **Detection**: Complex switch/if-elif chains
- **Signs**: Type checking, adding new types requires modification
- **Refactoring**: Replace Conditional with Polymorphism, Replace Type Code with State/Strategy

### Temporary Field
- **Detection**: Instance variables used only in certain circumstances
- **Signs**: Null/empty most of the time
- **Refactoring**: Extract Class, Replace Method with Method Object

### Refused Bequest
- **Detection**: Subclass uses only some inherited methods
- **Signs**: Empty method implementations
- **Refactoring**: Replace Inheritance with Delegation, Extract Superclass

### Alternative Classes with Different Interfaces
- **Detection**: Two classes do the same thing with different method names
- **Refactoring**: Rename Method, Move Method, Extract Superclass

## Change Preventers

### Divergent Change
- **Detection**: One class commonly changed for different reasons
- **Signs**: "When I add X, I need to change methods A, B, C"
- **Refactoring**: Extract Class, Split Phase

### Shotgun Surgery
- **Detection**: One change requires many small changes in many classes
- **Signs**: Making a change requires modifying many different classes
- **Refactoring**: Move Method, Move Field, Inline Class

### Parallel Inheritance Hierarchies
- **Detection**: Creating subclass requires creating subclass in another hierarchy
- **Signs**: Prefix/suffix patterns in class names
- **Refactoring**: Move Method, Move Field

## Dispensables

Code that is pointless and should be removed.

### Comments
- **Detection**: Comments explaining what code does
- **Signs**: Method/variable names don't reveal intent
- **Refactoring**: Extract Method, Rename Method, Extract Variable

### Duplicate Code
- **Detection**: Same code in multiple places
- **Measurement**: > 5% duplication critical
- **Refactoring**: Extract Method, Pull Up Method, Form Template Method

### Lazy Class
- **Detection**: Class doesn't do enough to justify existence
- **Signs**: Few methods, little functionality
- **Refactoring**: Inline Class, Collapse Hierarchy

### Data Class
- **Detection**: Class with only fields and getters/setters
- **Signs**: No behavior, just data container
- **Refactoring**: Move Method, Encapsulate Collection

### Dead Code
- **Detection**: Unused variables, parameters, methods, classes
- **Signs**: Never called, always False condition
- **Refactoring**: Delete

### Speculative Generality
- **Detection**: "We might need this someday"
- **Signs**: Unused abstract classes, unnecessary delegation
- **Refactoring**: Collapse Hierarchy, Inline Class, Remove Parameter

## Couplers

Features that contribute to excessive coupling.

### Feature Envy
- **Detection**: Method uses more features of another class
- **Signs**: Lots of calls to other class, few to own class
- **Refactoring**: Move Method, Extract Method

### Inappropriate Intimacy
- **Detection**: Classes know too much about each other's internals
- **Signs**: Accessing private fields, bidirectional relationships
- **Refactoring**: Move Method, Extract Class, Hide Delegate

### Message Chains
- **Detection**: a.getB().getC().getD()
- **Signs**: Long chains of method calls
- **Refactoring**: Hide Delegate, Extract Method

### Middle Man
- **Detection**: Class only delegates to another class
- **Signs**: Most methods just call another class
- **Refactoring**: Remove Middle Man, Inline Method

## Python-Specific Smells

### Not Using Context Managers
- **Detection**: Manual file.close(), db.commit(), try/finally
- **Refactoring**: Use `with` statement

### Not Using Comprehensions
- **Detection**: Simple for loops building lists/dicts
- **Refactoring**: List/dict comprehension

### Mutable Default Arguments
- **Detection**: `def func(arg=[]):`
- **Fix**: Use `def func(arg=None):` with `arg = arg or []`

### Using `range(len())`
- **Detection**: `for i in range(len(items)): items[i]`
- **Refactoring**: Use `enumerate(items)` or iterate directly

### Not Using Generators
- **Detection**: Building large lists in memory
- **Refactoring**: Use generator expressions or `yield`

## React/JavaScript-Specific Smells

### Prop Drilling
- **Detection**: Props passed through 3+ levels
- **Refactoring**: Use Context, composition, or state management

### God Component
- **Detection**: Component > 200 lines with multiple responsibilities
- **Refactoring**: Extract components, use custom hooks

### Inline Function Definitions
- **Detection**: `onClick={() => handleClick()}` on re-rendered components
- **Refactoring**: Use `useCallback`

### Missing Keys in Lists
- **Detection**: `.map()` without unique `key` prop
- **Fix**: Add stable unique key

### Unnecessary useEffect
- **Detection**: useEffect for derived state or synchronous operations
- **Refactoring**: Calculate during render or use useMemo

### Missing Dependencies in Hooks
- **Detection**: ESLint warning about exhaustive-deps
- **Fix**: Add missing dependencies or use refs

## Next.js-Specific Smells

### Client Component Overuse
- **Detection**: 'use client' when server component would work
- **Refactoring**: Keep as server component, extract only interactive parts

### Blocking Data Fetching
- **Detection**: Sequential awaits in Server Components
- **Refactoring**: Use Promise.all() or Suspense boundaries

### Not Using Next/Image
- **Detection**: `<img>` tags for content images
- **Refactoring**: Use `<Image>` component

### Route Handler for Static Data
- **Detection**: API route that returns static data
- **Refactoring**: Use Server Components directly

### Not Leveraging Caching
- **Detection**: Fetching same data repeatedly
- **Refactoring**: Use Next.js caching, React cache()

## Detection Tools

### Python
- **Pylint**: All-purpose linter
- **Radon**: Complexity metrics
- **Vulture**: Dead code detection
- **Bandit**: Security issues

### JavaScript/TypeScript
- **ESLint**: All-purpose linter
- **TypeScript**: Type errors
- **SonarQube**: Code quality metrics
- **Complexity-report**: Cyclomatic complexity

### Both
- **SonarQube**: Multi-language analysis
- **CodeClimate**: Maintainability metrics
- **CodeScene**: Behavioral analysis

## Severity Levels

### Critical
- Cyclomatic complexity > 20
- Maintainability index < 20
- Security vulnerabilities
- > 20% code duplication

### High
- Cyclomatic complexity 15-20
- Maintainability index 20-40
- Long methods (> 100 lines)
- Large classes (> 500 lines)

### Medium
- Cyclomatic complexity 10-15
- Maintainability index 40-65
- Long methods (50-100 lines)
- Long parameter lists (> 5)

### Low
- Cyclomatic complexity 5-10
- Code style issues
- Missing documentation
- Minor optimizations

## Refactoring Priority

1. **Security vulnerabilities** - Immediate
2. **Critical complexity** - Within sprint
3. **High complexity** - Next sprint
4. **Code duplication** - Ongoing
5. **Style issues** - As you go
