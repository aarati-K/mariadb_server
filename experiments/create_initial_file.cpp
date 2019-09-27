// Command: g++ -I/usr/include/mariadb -L/usr/lib/mariadb/ -lmariadb create_initial_file.cpp

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

#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>
#include <ctime>

using namespace std;

#define INPUT_FILE "/mnt/hdd/record/sqlite/initial_keys.txt"
#define KEY_BASE 0
#define NUM_ITERATIONS 200
#define NUM_INSERTIONS_PER_ITERATION 50000
#define NUM_FETCH_PER_ITERATION 0
#define NUM_INSERTIONS_PER_XACT_DEFAULT 50000

void generate_insert_stmt(int i, char* cmd_buffer) {
    char* temp = "vjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfhvjdkelanfh";
    sprintf(cmd_buffer, "INSERT INTO KV VALUES (%d, '%s');", i, temp);
}

void generate_select_stmt(int i, char* cmd_buffer) {
    sprintf(cmd_buffer, "SELECT V FROM KV WHERE K=%d;", i);
}

long getTimeDiff(struct timeval startTime, struct timeval endTime) {
    return (long)((endTime.tv_sec - startTime.tv_sec)*1000000 +
        (endTime.tv_usec - startTime.tv_usec));
}

int main(int argc, char** argv) {
    MYSQL *mysql;
    MYSQL_RES* res;
    int i, j, rc;
    long time_taken;
    int max_count = 1;
    ifstream input(INPUT_FILE);
    int insert_count;
    unsigned int key;
    struct timeval startTime, endTime;
    int num_insertions_per_transaction = NUM_INSERTIONS_PER_XACT_DEFAULT;
    if (argc >= 2) {
        num_insertions_per_transaction = stoi(argv[1]);
    }
    vector<int> keys_to_insert;
    vector<int> keys_to_fetch;
    vector<int> keys_present;
    vector<int>::iterator it;

    // Connect to mysql server
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

    // Initialize command buffer
    char* cmd_buffer = (char*)malloc(sizeof(char)*200);
    if (!cmd_buffer) {
        cout << "cmd_buffer malloc failed" << endl;
        return 1;
    }
    memset(cmd_buffer, 0, 200);

    // Check if input/output files are open
    if (!input.is_open()) {
        cout << "Could not open input file" << endl;
        return 1;
    }

    // Common seed
    srand(0);

    // initialize keys_present
    for (i=0; i<KEY_BASE; i++) {
        keys_present.push_back(i);
    }

    for(i=0; i<NUM_ITERATIONS; i++) {
        for (j=0; j<NUM_INSERTIONS_PER_ITERATION; j++) {
            input >> key;
            keys_to_insert.push_back(key + KEY_BASE);
        }

        // Start inserting keys
        time_taken = 0;
        insert_count = 0;
        for (it=keys_to_insert.begin(); it!=keys_to_insert.end(); it++) {
            generate_insert_stmt((*it), cmd_buffer);

            gettimeofday(&startTime, NULL);
            if (insert_count == 0) {
                // Begin transaction
                rc = mysql_query(mysql, "BEGIN;");
                if (rc != 0) {
                    cout << "Failed begin transaction iteration: " << i << endl;
                    goto out;
                }
            }

            rc = mysql_query(mysql, cmd_buffer);
            insert_count += 1;
            if (insert_count == num_insertions_per_transaction) {
                insert_count = 0;
                rc = mysql_query(mysql, "COMMIT;");
                if (rc != 0) {
                    cout << "Failed commit transaction iteration: " << i << endl;
                    goto out;
                }
            }
            gettimeofday(&endTime, NULL);

            if (rc != 0) {
                cout << "Failed inserting key " << (*it) << endl;
                goto out;
            }
            time_taken += getTimeDiff(startTime, endTime);
        }

        // Starting select operations
        keys_present.insert(keys_present.end(), keys_to_insert.begin(), keys_to_insert.end());
        keys_to_insert.clear();

        // Generate random keys to fetch
        for (j=0; j<NUM_FETCH_PER_ITERATION; j++) {
            key = keys_present[rand() % keys_present.size()];
            keys_to_fetch.push_back(key);
        }

        mysql_query(mysql, "BEGIN;");
        time_taken = 0;
        for (it=keys_to_fetch.begin(); it!=keys_to_fetch.end(); it++) {
            generate_select_stmt(*it, cmd_buffer);

            gettimeofday(&startTime, NULL);
            rc = mysql_query(mysql, cmd_buffer);
            gettimeofday(&endTime, NULL);

            res = mysql_use_result(mysql);
            mysql_free_result(res);

            if (rc != 0) {
                cout << "Failed fetching key " << (*it) << endl;
                goto out;
            }
            time_taken += getTimeDiff(startTime, endTime);
        }
        mysql_query(mysql, "COMMIT;");

        cout << "Finished iteration: " << i << endl;
        keys_to_fetch.clear();
    }

out:
    mysql_close(mysql);

close_files:
    input.close();
    return 0;
}
