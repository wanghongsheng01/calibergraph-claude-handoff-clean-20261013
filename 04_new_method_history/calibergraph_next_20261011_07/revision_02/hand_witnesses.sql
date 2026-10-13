-- Constructed by hand. NOT executed. No benchmark-derived values.
-- A: collision witness, two rows, legal primary key.
CREATE TABLE WitnessP (k INTEGER PRIMARY KEY, v INTEGER NOT NULL);
INSERT INTO WitnessP(k,v) VALUES (1,0),(2,0);
SELECT DISTINCT v FROM WitnessP; -- expected bag: [(0)]
SELECT v FROM WitnessP;          -- expected bag: [(0),(0)]

-- B: non-key-anchorable counted projection; acyclic foreign key.
CREATE TABLE WitnessCustomer (cid INTEGER PRIMARY KEY);
CREATE TABLE WitnessOrders (
  oid INTEGER PRIMARY KEY,
  cid INTEGER NOT NULL REFERENCES WitnessCustomer(cid)
);
INSERT INTO WitnessCustomer(cid) VALUES (1),(2);
INSERT INTO WitnessOrders(oid,cid) VALUES (11,1),(22,2);
SELECT 1 AS unit FROM (
  SELECT DISTINCT c.cid
  FROM WitnessCustomer c JOIN WitnessOrders o ON c.cid=o.cid
) d; -- expected bag: [(1),(1)]
SELECT DISTINCT 1 AS unit
FROM WitnessCustomer c JOIN WitnessOrders o ON c.cid=o.cid;
-- expected bag: [(1)]

-- C: finite-field cardinality reduction is not SQL semantics.
-- The combined-query cores are SELECT 1 FROM WitnessP and
-- SELECT 1 FROM WitnessP a CROSS JOIN WitnessP b (multiplicities 2 and 4).
-- The following COUNT queries are observers only, not a C-fragment extension.
SELECT COUNT(*) AS n FROM WitnessP; -- expected [(2)]
SELECT COUNT(*) AS n FROM WitnessP a CROSS JOIN WitnessP b; -- expected [(4)]
-- Both counts are 0 modulo 2. This is a false equality fingerprint.
