#include <string.h>
#include <stdlib.h>

// Function to return the obfuscated key
char* get_obfuscated_key() {
    // Random obfuscated key: split into parts and stored as ASCII codes
    const char part1[] = {98, 51, 100, 57, 50, 98, 54, 98, 57, 52, 57, 98, 101, 54, 99, 51, 54, 12, 100, 0}; // Added null terminator
    const char part2[] = {55, 54, 98, 57, 100, 51, 98, 51, 53, 52, 52, 101, 51, 101, 54, 49, 97, 54, 10, 0}; // Added null terminator
    const char part3[] = {55, 52, 51, 50, 57, 0, 100, 49, 102, 50, 97, 56, 52, 101, 102, 55, 52, 57, 0}; // Added null terminator
    const char part4[] = {53, 51, 99, 51, 101, 57, 102, 56, 50, 52, 99, 95, 57, 102, 56, 98, 49, 51, 52, 0}; // Added null terminator

    // Calculate total length (excluding the null terminators)
    size_t total_length = sizeof(part1) + sizeof(part2) + sizeof(part3) + sizeof(part4) - 4; // Subtracting 4 for null terminators
    char* key = (char*)malloc(total_length + 1); // +1 for the null terminator
    if (key == NULL) {
        return NULL;
    }

    // Assemble the full key from the parts
    strcpy(key, part1);
    strcat(key, part2);
    strcat(key, part3);
    strcat(key, part4);

    return key;
}
