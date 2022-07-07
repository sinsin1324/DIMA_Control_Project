#include <mutex>

int header, in_h, in_h2;
char cls1;
struct packet *command_qp, *current_command, command, command_queue[Q_SIZE];
int packet_pos, in_pp;
std::mutex q_lock, curr_lock;
