#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <ENV_VAR_NAME> [<ENV_VAR_NAME> ...]\n", argv[0]);
        return 1;
    }

    int all_found = 1;
    for (int i = 1; i < argc; i++) {
        const char *env_name = argv[i];
        const char *env_value = getenv(env_name);

        if (env_value != NULL) {
            printf("%s=%s\n", env_name, env_value);
        } else {
            fprintf(stderr, "ERROR: Environment variable '%s' not found\n", env_name);
            all_found = 0;
        }
    }

    return all_found ? 0 : 1;
}
