# Guidelines

## Directory Naming & Nomenclature

* Non-Project Folders: Formatted in PascalCase.
* Project Folders: Formatted in kebab-case.
* Project Sub-folders: Consist of a single lowercase word only.
* Files: Formatted in snake_case.
* Files & Packages: lower_snake_case (e.g., shopping_cart.py).
* Namespaces, Classes, Enums, Structs, Interfaces: PascalCase (e.g., ShoppingCart).
* Variables, Parameters, Functions & Methods: camelCase (e.g., addItem, totalAmount).
* Constants, Final and Global Variables: UPPER_SNAKE_CASE (e.g., MAX_ITEMS).

## Coding Structure & Formatting

* File Header: Every file must start with a header comment including the File Name and Purpose.
* Top-Level Imports: Imports must be placed at the very top of the file, immediately following the header comment.
* Top-Level Declarations: All Global, Final, Constant, and Static variables must be declared at the top of the file, immediately after the imports.
* Class/Enum Comments: Every Namespace, Class, Struct, Enum, Union, and Interface must have a short multiline comment explaining its purpose.
* Function/Method Comments: Every function/method must have a short multiline comment explaining its purpose, parameters (Takes), and return value (Gives) using this exact format:

```text
[Clear, concise description of the method/function's purpose]

Takes:
	[parameter_name] ([type]): [Description of what it takes].

Gives:
	[type]: [Description of what it returns].
```

* CRITICAL: Do not use single-line comments (# ...) under any circumstances. All comments must be block/multiline comments or docstrings.
* Structural Brackets: Brackets for Namespaces, Classes, Structs, Enums, Methods, and Functions must start on the next line.
* Conditional Brackets: Brackets for Conditional Statements must start on the same line.

## Branching & Commits

* Branch Naming: Use feature/ or defectfix/ or documentation/ or improvement/ prefixes for your branch names.
* Commit Messages: Follow the Conventional Commits specification (e.g., feat: add login).
* Atomic Commits: Keep your commits small and focused on a single change.

## Issues & Pullrequests

* Issue Templates: You must use the provided issue templates for all bugs or features.
* PR Templates: Fill out the Pull Request template completely when submitting code.
* Incomplete Submissions: Please don't submit blank issues or PRs. If you decide not to use the provided default template, make sure your text still includes all the core details the template asks for. Empty or uninformative submissions will be automatically closed.
* Link Issues: Always link your PR to an existing, approved issue.
* Review Process: Wait for at least one maintainer approval before merging.
* Be Responsive: Address review feedback or questions within a few days.
