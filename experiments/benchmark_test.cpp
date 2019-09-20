// Command: g++ -I/usr/include/mariadb -L/usr/lib/mariadb/ -lmariadb benchmark_test.cpp

// Testing the C API for MariaDB
#include <mysql.h>

// C++ includes
#include <iostream>
#include <fstream>
#include <string>
#include <vector>

// C includes
#include <cstring>
#include <cstdlib>
#include <cstdio>

using namespace std;

#define INPUT_FILE "/mnt/hdd/record/sqlite/initial_keys.txt"
#define KEY_BASE 0

void generate_insert_stmt(int i, char* cmd_buffer) {
    char* temp = "vjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfh";
    sprintf(cmd_buffer, "INSERT INTO KV VALUES (%d, '%s');", i, temp);
}

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
        cout << "drop table: " << mysql_error(mysql) << endl;
        return 1;
    }

    // Create table KV
    if (mysql_query(mysql, "CREATE TABLE KV (K INT NOT NULL PRIMARY KEY,"\
                            "V CHAR(100) DEFAULT 'empty')")) {
        // cout << "Error while creating table" << endl;
        cout << "create table: " << mysql_error(mysql) << endl;
        return 1;
    }

    char* cmd_buffer = (char*)malloc(sizeof(char)*200);
    if (!cmd_buffer) {
        cout << "cmd_buffer malloc failed" << endl;
        return 1;
    }
    memset(cmd_buffer, 0, 200);
    // generate_insert_stmt(1, cmd_buffer);
    // cout << cmd_buffer << endl;
    ifstream input(INPUT_FILE);
    if (!input.is_open()) {
        cout << "Could not open input file" << endl;
        return 1;
    }
    int key, i;
    vector<int> keys_to_insert;
    vector<int>::iterator it;
    int max_count = 100;

    i = 0;
    while (input >> key) {
        keys_to_insert.push_back(KEY_BASE + key);
        i += 1;
        if (i==max_count) {
            break;
        }
    }
    cout << "Total key count: " << keys_to_insert.size() << endl;;
    input.close();

    for (it=keys_to_insert.begin(); it!=keys_to_insert.end(); it++) {
        generate_insert_stmt(*it, cmd_buffer);
        if (mysql_query(mysql, cmd_buffer)) {
            cout << "Insert: " << mysql_error(mysql) << endl;
            return 1;
        }
    }

    mysql_close(mysql);
    return 0;
}
