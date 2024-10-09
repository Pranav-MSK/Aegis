#include "obfuscation.h"
#include <string.h>
#include <stdlib.h>

// Function to return the obfuscated key
char* get_obfuscated_key() {
    // Obfuscated key: split into parts and stored as ASCII codes
    const char part1[] = {51, 115, 83, 48, 77, 95, 0};
    const char part2[] = {122, 113, 67, 75, 50, 74, 104, 86, 55, 88, 56, 49, 69, 66, 75, 111, 0};
    const char part3[] = {90, 106, 73, 49, 117, 118, 49, 117, 55, 122, 49, 106, 76, 118, 87, 115, 111, 89, 97, 70, 103, 61, 0};

    // Allocate memory for the full key
    char* key = (char*)malloc(strlen(part1) + strlen(part2) + strlen(part3) + 1);
    if (key == NULL) {
        return NULL;
    }

    // Assemble the full key from the parts
    strcpy(key, part1);
    strcat(key, part2);
    strcat(key, part3);

    return key;
}
