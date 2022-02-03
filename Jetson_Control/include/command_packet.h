#include <stdio.h>
#include <stdint.h>

//percentages between -100 and 100
struct actuator_commands {
    float throttle;
    float steering;
    float tail_velocity;
    float aux2;
};

//control commands, speed in m/s and rest in radians
struct control_loop_commands {
    float speed;
    float heading;
    float position;
    float damper;

};

//general header command
struct command_header {
    uint16_t crc;
    uint16_t cls;
    uint16_t length;
};

//system mode commands
typedef uint8_t system_mode_command;    //bit 7:6 throttle
                                //bit 4:5 steering
                                //bit 2:3 aux1
                                //bit 0:1 aux2
                                // 00 manual 01 auto 10 control

union data_packet {
    struct control_loop_commands c_loop_commands;
    struct actuator_commands c_actuator;
    system_mode_command c_system_mode;
};

struct packet {
    struct command_header c_header;
    union data_packet c_data;
};
