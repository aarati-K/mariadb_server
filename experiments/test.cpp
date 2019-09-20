// Command: g++ -I/usr/include/mariadb -L/usr/lib/mariadb/ -lmariadb test.cpp

// Testing the C API for MariaDB

#include <mysql.h>
#include <iostream>

using namespace std;

int main() {
    MYSQL *mysql;
    mysql= mysql_init(NULL);
    if (!mysql_real_connect(mysql, "localhost", "aarati", "tiaara123*", "test", 0, "/tmp/mysql.sock", 0)) {
        mysql_error(mysql);
    } else {
        cout << "Connected to the database server" << endl;
    }

    // Drop existing KV table
    if (mysql_query(mysql, "DROP TABLE IF EXISTS KV")) {
        // cout << "Error while dropping table" << endl;
        cout << mysql_error(mysql) << endl;
        return 1;
    }

    // Create table KV
    if (mysql_query(mysql, "CREATE TABLE KV (K INT NOT NULL PRIMARY KEY,"\
                            "V CHAR(100) DEFAULT 'empty')")) {
        // cout << "Error while creating table" << endl;
        cout << "create table: " << mysql_error(mysql) << endl;
        return 1;
    }

    // Run an insert query -- worked!
    if (mysql_query(mysql, "INSERT INTO KV VALUES (1, 'vjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfh')")) {
        cout << "insert: " << mysql_error(mysql) << endl;
        return 1;
    }

    mysql_close(mysql);
	return 0;
}
