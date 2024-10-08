#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#define LOG_FILE "logs/app_debug.log"

void log_message(const char *level, const char *message) {
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

