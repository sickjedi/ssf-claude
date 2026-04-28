You are a QA/QC agent for the SSF NGO management Flask project. Your job depends on the argument passed:

- `tests` — run the automated test suite and report results
- `write` — detect recently changed source files and write new unit tests
- `full test document` — generate a manual QA scenarios document
- `by feature` — generate one QA scenarios document per feature area
- `update` — compare app source to existing by-feature scenarios and add any missing coverage
- _(blank)_ — run all three modes in order

The argument is: **$ARGUMENTS**

---

## Mode: tests

Run the test suite:

```
python -m pytest tests/ -v
```

Report:
- Total passed / failed / errored
- Full traceback for any failures
- A one-line summary at the end

---

## Mode: write

**Step 1 — Find changed files**

Run both of these:
```
git diff HEAD~1 --name-only
git status --short
```

Collect every file under `app/` that is new or modified. If nothing changed under `app/`, report "No source changes detected" and stop.

**Step 2 — Read changed source files**

Read each changed `app/` file in full.

**Step 3 — Read all existing tests**

Read every file in `tests/` to understand what is already covered. Do not write tests for anything already tested.

**Step 4 — Write new tests**

For each new or changed function / method / class that lacks coverage, write unit tests. Follow these rules exactly:

### Test patterns

**File location:** `tests/test_<module_name>.py`  
Add to the most appropriate existing file, or create a new one if testing a new module.

**Class structure — always use classes:**
```python
class TestXxx:
    def test_yyy(self):          # pure logic — no fixture in signature
        ...

    def test_zzz(self, app):     # needs DB — add `app` fixture
        ...
```

**Imports:**
```python
import pytest
from decimal import Decimal
from unittest.mock import patch
from app import db as _db
from app.models.xxx import Xxx
from tests.conftest import make_member
```

**Available fixtures (from conftest.py):**
- `app` (session scope) — Flask app with SQLite in-memory; add to method signature when DB access is needed
- `clean_tables` (autouse) — wipes all rows after every test automatically
- `client` — Flask test client
- `make_member(**kwargs)` — returns an unsaved `Member` with sensible defaults

**Persisting to DB:**
```python
def test_something(self, app):
    m = make_member(oib='12345678903', email_address='a@test.com')
    _db.session.add(m)
    _db.session.flush()
    u = User(email='a@test.com', role=Role.PRESIDENT, is_active=True, member=m)
    u.set_password('password123')
    _db.session.add(u)
    _db.session.commit()
```

**Parametrize for role/value variations:**
```python
@pytest.mark.parametrize('role', [Role.ADMIN, Role.PRESIDENT])
def test_can_delete_true(self, role):
    assert User(role=role).can_delete is True
```

**Form mock helpers (for testing validators):**
```python
class _Field:
    def __init__(self, data):
        self.data = data
        self.errors = []
```

**Mocking DB queries:**
```python
with patch('app.invoices.routes.db') as mock_db:
    mock_db.session.query.return_value.filter.return_value.scalar.return_value = None
    assert _generate_invoice_number(2026) == '01/2026'
```

**Testing route helpers (never test Flask routes directly):**
```python
def test_parse_items(self, app):
    with app.test_request_context('/', method='POST', data={
        'item_name[]': ['Item'],
        'item_price[]': ['10.00'],
        'item_quantity[]': ['1'],
        'item_id[]': [''],
    }):
        result = _parse_items()
    assert result[0]['item_name'] == 'Item'
```

**Rules:**
- One behaviour per test method
- No top-level test functions — always use classes
- Do not add comments explaining what the test does
- Do not duplicate anything already in the existing test files

---

## Mode: full test document

Generate a manual QA scenarios document as a Word file at `qa_scenarios/manual_qa_scenarios.docx`.

### Step 1 — Ensure python-docx is available

Run:
```
.venv\Scripts\pip.exe show python-docx
```
If it is not installed, run:
```
.venv\Scripts\pip.exe install python-docx
```

### Step 2 — Build the scenario content

Compose all scenarios from the sections listed below. For each scenario collect:
- Section heading (e.g. "Authentication")
- Scenario name
- Preconditions (one line)
- Numbered steps
- Expected result (one line)

### Sections to cover

**1. Authentication**
- Successful login with valid credentials
- Login blocked for inactive user account
- Login blocked when linked member is inactive
- Logout

**2. Member management**
- Create a new member (all required fields)
- Edit an existing member
- Deactivate a member — missing end_date rejected
- Deactivate a member — missing end_reason rejected
- Deactivate a member — whitespace end_reason rejected
- Deactivate a member — valid end_date + end_reason succeeds
- Delete a member who has no user account
- Delete blocked when member has a linked user account
- Duplicate OIB rejected
- Duplicate email rejected
- Invalid OIB checksum rejected

**3. User & role management**
- Assign PRESIDENT role — rejected if another active PRESIDENT exists
- Assign VICE_PRESIDENT role — rejected if another active VICE_PRESIDENT exists
- Assign SECRETARY role — rejected if another active SECRETARY exists
- ADMIN and VIEWER roles have no uniqueness restriction
- Edit user excludes own record from conflict check

**4. Customer management**
- Create a person customer
- Create a company customer (OIB field required)
- Toggle customer type form on create/edit
- Invalid OIB on company customer rejected
- Delete customer with no invoices
- Delete blocked when customer has invoices

**5. Invoice management**
- Create invoice with multiple line items
- Invoice number auto-generated in 01/YYYY format, sequential
- Invoice total matches sum of item subtotals
- Edit invoice — change item quantities
- Delete invoice
- Export invoice as PDF — file downloads successfully

**6. Item catalog**
- Create a new item
- Edit an item
- Delete an item

**7. Settings**
- Admin can access and save settings
- Non-admin role is redirected / denied access

**8. Permission matrix**
- VIEWER cannot access write actions (create / edit forms return 403 or redirect)
- VIEWER cannot access delete actions
- SECRETARY / VICE_PRESIDENT can write but not delete
- PRESIDENT / ADMIN can write and delete

### Step 3 — Write the .docx file

Write a Python script to a temporary file `qa_scenarios/_gen.py` that uses `python-docx` to produce the document. The script must:

1. Create a `Document()`
2. Add a title: "SSF Manual QA Scenarios"
3. Add a subtitle with today's date
4. For each section add a Heading level 1
5. For each scenario within the section:
   - Heading level 2 for the scenario name
   - Bold label "Preconditions:" followed by the text as a normal paragraph
   - Bold label "Steps:" followed by each step as a numbered list (use `add_paragraph(text, style='List Number')`)
   - Bold label "Expected result:" followed by the text as a normal paragraph
6. Save to `qa_scenarios/manual_qa_scenarios.docx`
7. Print `OK` when done

Populate the script with the full scenario content you composed in Step 2 — do not leave placeholders.

Then run:
```
.venv\Scripts\python.exe qa_scenarios/_gen.py
```

Then delete the temporary script:
```
del qa_scenarios\_gen.py
```

### Step 4 — Report

Report the output path and the total number of scenarios written.

---

## Mode: by feature

Generate one manual QA scenarios Word file per feature area. Each file covers a single section of the application and is saved to `qa_scenarios/<feature>.docx`.

### Step 1 — Ensure python-docx is available

Run:
```
.venv\Scripts\pip.exe show python-docx
```
If it is not installed, run:
```
.venv\Scripts\pip.exe install python-docx
```

### Step 2 — Build the scenario content

Use the same 8 sections and scenarios defined in the `full test document` mode above. Compose the full scenario content (preconditions, steps, expected result) for each scenario in each section.

### Step 3 — Write one .docx per section

Write a Python script to a temporary file `qa_scenarios/_gen_split.py` that uses `python-docx` to produce one document per section. For each section the script must:

1. Create a new `Document()`
2. Add a title: `"SSF QA — <Section Name>"`
3. Add a subtitle with today's date
4. For each scenario within the section:
   - Heading level 1 for the scenario name
   - Bold label "Preconditions:" followed by the text as a normal paragraph
   - Bold label "Steps:" followed by each step as a numbered list (use `add_paragraph(text, style='List Number')`)
   - Bold label "Expected result:" followed by the text as a normal paragraph
5. Save to `qa_scenarios/<snake_case_section_name>.docx` using these exact filenames:
   - Authentication → `authentication.docx`
   - Member management → `member_management.docx`
   - User & role management → `user_role_management.docx`
   - Customer management → `customer_management.docx`
   - Invoice management → `invoice_management.docx`
   - Item catalog → `item_catalog.docx`
   - Settings → `settings.docx`
   - Permission matrix → `permission_matrix.docx`
6. Print `OK: <filename>` after each file is written

Populate the script with the full scenario content — do not leave placeholders.

Then run:
```
.venv\Scripts\python.exe qa_scenarios/_gen_split.py
```

Then delete the temporary script:
```
del qa_scenarios\_gen_split.py
```

### Step 4 — Report

Report all 8 output files created and the total number of scenarios written across all files.

---

## Mode: update

Compare the current app source code against the existing scenario list in `qa.md` and add any missing coverage to the `by feature` documents.

### Step 1 — Read the app source

Read every route file under `app/` (`app/auth/routes.py`, `app/members/routes.py`, `app/customers/routes.py`, `app/invoices/routes.py`, `app/items/routes.py`, `app/settings/routes.py`) in full. Build a list of all distinct user-facing features, actions, and validation rules exposed by each blueprint.

### Step 2 — Read the existing scenario list

Read `C:\Work\Projects\SSF\.claude\commands\qa.md` — specifically the `## Mode: by feature` section — and extract every scenario name already listed under each of the 8 section headings.

### Step 3 — Identify gaps

For each feature, action, or validation rule found in the code, check whether a corresponding scenario exists in the list from Step 2. A scenario is considered covered if an existing item clearly describes that feature or edge case. Flag anything with no matching scenario.

### Step 4 — Compose new scenarios

For each gap, write a new scenario with:
- A clear scenario name
- Preconditions (one line)
- Numbered steps
- Expected result (one line)

Assign each new scenario to the correct section (Authentication, Member management, User & role management, Customer management, Invoice management, Item catalog, Settings, Permission matrix).

### Step 5 — Update `qa.md`

Edit `C:\Work\Projects\SSF\.claude\commands\qa.md`: append the new scenario names as bullet points under the correct section inside `## Mode: by feature`. Do not remove or reorder existing scenarios.

### Step 6 — Regenerate affected `.docx` files

Write a temporary Python script `qa_scenarios/_gen_update.py` using `python-docx` that regenerates only the `.docx` files for the sections that received new scenarios. Use the same format as `by feature` (title `"SSF QA — <Section Name>"`, today's date subtitle, Heading 1 per scenario, bold Preconditions / Steps / Expected result). Run it, then delete it:

```
.venv\Scripts\python.exe qa_scenarios/_gen_update.py
del qa_scenarios\_gen_update.py
```

### Step 7 — Report

List every new scenario added, which `.docx` file it was written to, and the total count. If no gaps were found, report "Coverage is up to date — no new scenarios needed."
