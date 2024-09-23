import sys
import os
import subprocess
import threading
import queue
import argparse
import re
from datetime import datetime

# Default chunk size in bytes (4KB)
default_chunk_size = 165536

# Default intervals for updates
default_lines_per_update = 100000000   # Update console every 100,000 lines
default_chunks_per_update = 100000   # Update console every 50,000 chunks

# Path to the 7z executable (Update this with the correct path if needed)
seven_zip_path = "C:\\Program Files\\7-Zip\\7z.exe"  # Update this path if 7z.exe is not in your PATH

# Maximum output file size for test mode (10MB)
max_test_file_size = 10 * 1024 * 1024  # 10 MB

# Determine the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

def format_message(symbol, message):
    """Format the message with different symbols for clarity, including a timestamp."""
    symbol_map = {
        "Info": '[INFO]',
        "Progress": '[PROGRESS]',
        "Error": '[ERROR]',
        "Stopping": '[STOPPING]',
        "Chunk": '[CHUNK]'
    }
    formatted_symbol = symbol_map.get(symbol, f"[{symbol}]")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"{timestamp} {formatted_symbol} {message}"

def search_in_archive(archive_path, password, search_term, chunk_size, lines_per_update, chunks_per_update, results_filename, test_mode=False, verbose=False, buffer=False):
    """Search within the archive using 7z and output progress to the console."""
    start_time = datetime.now()  # Record the start time
    print(format_message("Info", f"Search started at {start_time}"))

    try:
        # Use subprocess to call the 7z command for streaming extraction
        command = [
            seven_zip_path, 'x', '-so', archive_path
        ]

        # Add the password option if a password is provided
        if password:
            command.insert(3, f'-p{password}')

        print(format_message("Info", f"Running command: {' '.join(command)}"))

        # Start the subprocess with both stdout and stderr piped
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=chunk_size)

        # Create queues for stdout and stderr
        output_queue = queue.Queue()

        # Create threads to read stdout and stderr separately
        stdout_thread = threading.Thread(target=read_stdout, args=(process, output_queue, search_term, chunk_size, lines_per_update, chunks_per_update, results_filename, test_mode, verbose, buffer))
        stderr_thread = threading.Thread(target=read_stderr, args=(process,))

        # Set threads as daemon so they exit when the main program exits
        stdout_thread.daemon = True
        stderr_thread.daemon = True

        stdout_thread.start()
        stderr_thread.start()

        # Wait for the threads to finish, with a timeout for stderr thread
        stdout_thread.join()
        stderr_thread.join(timeout=5)  # Wait for max 5 seconds for stderr thread

    except Exception as e:
        print(format_message("Error", f"Failed to search in archive: {e}"))
    finally:
        # Ensure the subprocess is terminated
        process.terminate()
        process.wait()

        stop_time = datetime.now()  # Record the stop time
        print(format_message("Info", f"Search complete. Finished at {stop_time}"))
        print(format_message("Info", f"Total run time: {stop_time - start_time}"))

def read_stdout(process, output_queue, search_term, chunk_size, lines_per_update, chunks_per_update, results_filename, test_mode, verbose, buffer):
    """Read and process the stdout output from the 7z process."""
    line_number = 0
    chunk_count = 0
    result_buffer = []  # Buffer to hold output before writing

    # Compile the search term as a regular expression
    search_regex = re.compile(re.escape(search_term), re.IGNORECASE)

    # Only open the results file if buffering is not enabled
    results_file = open(results_filename, 'wb') if not buffer else None

    try:
        while True:
            try:
                # Check file size in test mode
                if test_mode and results_file and results_file.tell() >= max_test_file_size:
                    print(format_message("Info", "Test mode: Output file size reached 10MB. Stopping..."))
                    break

                # Read a chunk from stdout
                output = process.stdout.read(chunk_size)
                if not output:
                    print(format_message("Info", f"End of stdout stream reached after {chunk_count} chunks."))
                    break  # End of stream

                chunk_count += 1

                # Decode the chunk output and split it into lines
                lines = output.decode(errors='ignore').splitlines()

                for line in lines:
                    line_number += 1
                    # Search for the term in each line
                    if search_regex.search(line):
                        result_message = format_message("Info", f"Found at line {line_number}: {line.strip()}")
                        output_queue.put(result_message)
                        result_buffer.append(result_message + '\n')  # Add to buffer
                        if verbose:  # Print to console if verbose mode is enabled
                            print(result_message)

                    # Display progress based on the user-defined interval
                    if line_number % lines_per_update == 0:
                        print(format_message("Progress", f"Processed {line_number} lines..."))

                # Write buffered results to the file less frequently if not buffering in memory
                if not buffer and len(result_buffer) > 100:  # Write only when buffer reaches 100 lines
                    results_file.write(''.join(result_buffer).encode())
                    result_buffer = []  # Clear the buffer

                # Display progress based on the user-defined chunk interval
                if chunk_count % chunks_per_update == 0:
                    print(format_message("Chunk", f"Processed chunk {chunk_count}"))

            except Exception as e:
                print(format_message("Error", f"Error reading chunk {chunk_count}: {e}"))
                break

        # Final write of remaining buffered data if not buffering in memory
        if not buffer and result_buffer:
            results_file.write(''.join(result_buffer).encode())

        # If buffering in memory, write all buffered results to the file at the end
        if buffer and result_buffer:
            with open(results_filename, 'wb') as results_file:
                results_file.write(''.join(result_buffer).encode())

    finally:
        if results_file:
            results_file.close()

def read_stderr(process):
    """Read and process the stderr output from the 7z process."""
    while True:
        try:
            # Read from stderr
            error_output = process.stderr.read(4096)
            if not error_output:
                print(format_message("Info", "End of stderr stream reached."))
                break  # End of stream

            print(format_message("Error", error_output.strip().decode()))

        except Exception as e:
            print(format_message("Error", f"Error reading from stderr: {e}"))
            break

def main():
    """Main function to handle command-line arguments and start the search."""
    print(format_message("Info", "Starting search in archive."))  # Initial start message with timestamp

    parser = argparse.ArgumentParser(
        description="Search within a 7z archive.",
        formatter_class=argparse.RawTextHelpFormatter,  # Preserve formatting in help text
        usage='''

    search_in_archive.py --path <archive> --search <term> [options]

    Required arguments:
      --path                  Path to the 7z archive
      --search                Search term to look for in the archive (Use quotes with spaces)

    Optional arguments:
      --password              Password for the 7z archive
      --verbose               Enable verbose mode to print search results to the console (Default: OFF) [Verbose OFF will increase search speed]
      --buffer                Keep results in buffer and write to file at the end (Default: OFF) [Buffer ON will increase search speed, but may lose results if crash or break]

      --chunk_size            Chunk size for reading (in bytes). (Default: 165536)
      --line_update_interval  Number of lines to process before printing progress. (Default: 100000000)
      --chunk_update_interval Number of chunks to process before printing chunk progress. (Default: 100000)

      --test                  Run in test mode, stop when output file reaches 10MB [Use for estimating parse times]

    Example: [Suggest to run with this command first to verify output and stability]
      search_in_archive.py --path archive.7z --search keyword --password SecretPassword --buffer --test
    '''
    )

    parser.add_argument('--path', required=True, help="Path to the 7z archive")
    parser.add_argument('--search', required=True, help="Search term to look for in the archive")

    parser.add_argument('--password', help="Password for the 7z archive (optional)")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose mode to print search results to the console")
    parser.add_argument('--buffer', action='store_true', help="Keep results in buffer and write to file at the end")

    parser.add_argument('--chunk_size', type=int, default=default_chunk_size, help="Chunk size for reading (in bytes)")
    parser.add_argument('--line_update_interval', type=int, default=default_lines_per_update, help="Number of lines to process before printing progress")
    parser.add_argument('--chunk_update_interval', type=int, default=default_chunks_per_update, help="Number of chunks to process before printing chunk progress")

    parser.add_argument('--test', action='store_true', help="Run in test mode, stop when output file reaches 10MB")

    args = parser.parse_args()

    archive_path = args.path
    search_term = args.search
    password = args.password
    chunk_size = args.chunk_size
    lines_per_update = args.line_update_interval
    chunks_per_update = args.chunk_update_interval
    test_mode = args.test
    verbose = args.verbose
    buffer = args.buffer

    # Generate a unique filename for the results
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    results_filename = os.path.join(script_dir, f"results_{timestamp}.txt")

    # Start searching in the archive
    search_in_archive(archive_path, password, search_term, chunk_size, lines_per_update, chunks_per_update, results_filename, test_mode, verbose, buffer)

if __name__ == "__main__":
    main()
