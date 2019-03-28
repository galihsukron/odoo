'''
Created on Jun 17, 2016

@author: qc
'''
import _mssql
conn = _mssql.connect(server= r'TONY-PC\MSSQL2008R2', user='tas', password='tas', \
    database='odoo2')
#conn.execute_non_query('CREATE TABLE persons(id INT, name VARCHAR(100))')
#conn.execute_non_query("INSERT INTO persons VALUES(1, 'John Doe')")
#conn.execute_non_query("INSERT INTO persons VALUES(2, 'Jane Doe')")
# how to fetch rows from a table
conn.execute_query('select top 10 * from res_users')
for row in conn:
    print "ID=%d, Name=%s" % (row['id'], row['name'])