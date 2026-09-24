# 03 — Student Schema (planning notes)

This is the plan for the data a single **Student** record will hold. No code has been written for it yet. It is the design that comes before the code.

## The fields

| Field        | Type     | Required?       | Validation rule                                  |
|--------------|----------|-----------------|--------------------------------------------------|
| `id`         | integer  | No (generated)  | Client can't set it                              |
| `name`       | string   | Yes             | Not empty; max 100 characters                    |
| `email`      | string   | Yes             | Must contain `@`; must be unique (else **409**)  |
| `age`        | integer  | Yes             | Must be a number; between 5 and 100              |
| `created_at` | datetime | No (automatic)  | Client can't set it                              |

## Why each rule is there

- **`id`: generated, not set by the client.** The server hands out IDs so that two records can never share one and a client can't pick or overwrite someone else's ID.
- **`name`: not empty, max 100 characters.** An empty name makes the record useless. The limit stops huge inputs and keeps the data tidy.
- **`email`: must contain `@`.** This is a light sanity check. It catches obvious typos but doesn't prove the address really exists.
- **`email`: must be unique.** Each student is identified by their own email, so two records with the same email would be a duplicate person.
- **Why 409 for a duplicate email?** HTTP status **409 Conflict** means the request was well-formed but clashes with data that already exists. That's different from **400 Bad Request**, which means the input itself is invalid (like an empty name).
- **`age`: a number from 5 to 100.** Storing age as a number means it can be compared and sorted. The range rules out impossible values like `-3` or `500`.
- **`created_at`: automatic.** The server records when the student was added. If the client could set it, the timestamp couldn't be trusted.

## Two kinds of fields

- **Client-supplied:** `name`, `email`, `age`. The user sends these, so they need validating.
- **Server-controlled:** `id`, `created_at`. The system fills these in, and the client is never allowed to set them.
