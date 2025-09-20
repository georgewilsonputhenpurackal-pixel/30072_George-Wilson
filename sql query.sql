
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    manager_id INTEGER REFERENCES employees(employee_id)
);

-- Insert sample data for managers and employees
-- First, insert the managers, as they don't report to anyone yet.
INSERT INTO employees (name, manager_id) VALUES
('Jane Doe', NULL),
('John Smith', NULL);

-- To get the IDs of the managers for the next inserts,
-- you can use a subquery or manually find them.
-- Assuming Jane Doe is employee_id 1 and John Smith is employee_id 2:
-- You can verify this by running: SELECT * FROM employees;

-- Now, insert employees and assign them a manager_id
INSERT INTO employees (name, manager_id) VALUES
('Alex Johnson', 1),  -- Reports to Jane Doe (ID 1)
('Emily Davis', 1),   -- Reports to Jane Doe (ID 1)
('Chris Wilson', 2),  -- Reports to John Smith (ID 2)
('Maria Rodriguez', 2); -- Reports to John Smith (ID 2)
