#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <errno.h>

#define LOG_DIR "logs"
#define LOG_FILE "logs/app_debug.log"

void create_log_dir() {
    struct stat st = {0};
    if (stat(LOG_DIR, &st) == -1) {
        if (mkdir(LOG_DIR, 0700) == -1) {
            perror("Error creating log directory");
        }
    }
}

void log_message(const char *level, const char *message) {
    create_log_dir();  // Ensure the log directory exists

    FILE *file = fopen(LOG_FILE, "a");
    if (file == NULL) {
        perror("Error opening log file");
        return;
    }

    // Get the current time
    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);
    if (tm_info == NULL) {
        perror("Error getting local time");
        fclose(file);
        return;
    }

    // Format the timestamp
    char timestamp[30];
    if (strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", tm_info) == 0) {
        fprintf(stderr, "Error formatting time\n");
        fclose(file);
        return;
    }

    // Write the log entry
    fprintf(file, "%s - %s - %s\n", timestamp, level, message);
    fclose(file);  // Close the log file
}
