#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>

void executePythonScript() {
    char *args[] = {"python", "Main.py", NULL};
    execv("/usr/bin/python3", args);
    perror("execv");
    exit(1);
}


int main() {
    while(1)
    {
        // Get the current time
        time_t curr = time(NULL);

        // Convert the current time to a local time structure
        struct tm *localTime = localtime(&curr);

        // Set the desired time (9:10) for the start time
        struct tm start_s = {
            .tm_sec = 0,
            .tm_min = 10,
            .tm_hour = 9,
            .tm_mday = localTime->tm_mday,
            .tm_mon = localTime->tm_mon,
            .tm_year = localTime->tm_year
        };

        // Set the desired time (15:30) for the end time
        struct tm end_s = {
            .tm_sec = 0,
            .tm_min = 30,
            .tm_hour = 15,
            .tm_mday = localTime->tm_mday,
            .tm_mon = localTime->tm_mon,
            .tm_year = localTime->tm_year
        };

        // Convert the start time structure to a time value
        time_t start = mktime(&start_s);

        // Convert the end time structure to a time value
        time_t end = mktime(&end_s);

        if (curr >= start && curr < end)
        {
            printf("inside\n");
            pid_t pid = fork();

            if (pid == 0) {
                // Child process
                executePythonScript();
            }
            else{
                int status;
                printf("Python script started. PID: %d\n", pid);
                wait(&status);
                printf("Python script stopped. PID: %d\n", pid);
            }
            
        }
        sleep(60);
    }
}