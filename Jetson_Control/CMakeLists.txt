cmake_minimum_required(VERSION 3.10.2)

project(jetson_control)

set(THREADS_PREFER_PTHREAD_FLAG ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ../bin)

add_executable(jetson_control src/jetson.cpp)

find_package(Threads REQUIRED)
target_link_libraries(jetson_control PRIVATE Threads::Threads)
find_package(JetsonGPIO REQUIRED)
target_link_libraries(jetson_control PRIVATE JetsonGPIO::JetsonGPIO)


