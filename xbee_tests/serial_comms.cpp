#include <sys/file.h>
#include <stdio.h>
#include <string.h>
#include<ctype.h>
#include <fcntl.h> // Contains file controls like O_RDWR
#include <errno.h> // Error integer and strerror() function
#include <termios.h> // Contains POSIX terminal control definitions
#include <unistd.h> // write(), read(), close()
#include <string>

void initPort(int *xbee_port) {
    struct termios tty;

    //change configuration settings for serial ports
    tcgetattr(*xbee_port, &tty);

    //set parity bit
    tty.c_cflag &= ~PARENB;

    //clear stop bit - one stop bit used
    tty.c_cflag &= ~CSTOPB;

    //set number of bits per byte
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8; // 8 bits per byte

    //disable hardware flow control
    tty.c_cflag &= ~CRTSCTS;

    //disable xon/xoff
    tty.c_iflag &= ~(IXON | IXOFF | IXANY);

    //turn on read, ignore control lines
    tty.c_cflag |= CREAD | CLOCAL;

    //disable canonical mode
    tty.c_lflag &= ~ICANON;

    //disable extra bits which are rendered useless by canonical mode
    tty.c_lflag &= ~ECHO; // Disable echo
    tty.c_lflag &= ~ECHOE; // Disable erasure
    tty.c_lflag &= ~ECHONL; // Disable new-line echo

    //disable signal chars
    tty.c_lflag &= ~ISIG;

    //disable special byte handling
    tty.c_iflag &= ~(IGNBRK|BRKINT|PARMRK|ISTRIP|INLCR|IGNCR|ICRNL);
    
    //disable output handling of of bytes
    tty.c_oflag &= ~OPOST;
    tty.c_oflag &= ~ONLCR;

    //setting minimum characters to be read and timeout
    tty.c_cc[VMIN] = 6;
    tty.c_cc[VTIME] = 10; //tenths of a second

    // Set in/out baud rate to be 230400
    cfsetispeed(&tty, B230400);
    cfsetospeed(&tty, B230400);
    
    // Save tty settings, also checking for error
    tcsetattr(*xbee_port, TCSANOW, &tty);
}

int main() {

    // int xbee_port = open("/dev/tty.usbserial-DN02SSJ0", O_RDWR | O_NOCTTY | O_NDELAY);
    int xbee_port = open("/dev/ttyUSB0", O_RDWR | O_NOCTTY | O_NDELAY);

    if (xbee_port < 0) {
        printf("Error %i from open: %s\n", errno, strerror(errno));
    }

    initPort(&xbee_port);
    FILE *fp;
    int c;
    // fp = fopen("/dev/tty.usbserial-DN02SSJ0", "r+");
    fp = fopen("/dev/ttyUSB0", "r+");
    if (fp) {
        while ((c = getc(fp)) != EOF){
            if (isdigit(c) || c == ' ' || c == '.' || c == '-' || c == '+') putchar(c);
            sleep(0.05);
        }
        fclose(fp);
    }
    return 0;   
}

