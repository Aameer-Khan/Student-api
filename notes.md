Field	Type	Required?	Validation rule
id	integer	No (generated)	Client can't set it
name	string	Yes	Not empty; max 100 characters
email	string	Yes	Must contain @; must be unique (else 409)
age	integer	Yes	Must be a number; between 5 and 100
created_at	datetime	No (automatic)	Client can't set it
