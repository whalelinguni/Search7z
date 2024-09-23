
# Search in 7z Archive Script

This Python script allows you to search for a specific term within a 7z archive file.

I was originally trying to multi-thread this out for faster parsing, but since have kinda given up on that. 

Options in place but have little impact on search speed without any multithreading.

With a really old i5 it takes on average 20-30 min to parse a ~20gb 7z compressed archive (~120gb decompressed) that contains a single txt file.

## Features

- **Search within 7z archives:** Reads out the archive in chunks to allow searching without needing to fully decompress.
- **Optional password protection:** Allows searching within password-protected archives.
- **Configurable chunk size:** Adjusts the chunk size for reading from the archive.
- **Progress updates:** Configurable intervals for updating the console with the current progress.
- **Buffering option:** Optionally buffer results in memory for faster processing.
- **Verbose mode:** Enable or disable printing of search results to the console.
- **Test mode:** Runs in test mode to stop when the output file reaches 10MB, useful for estimating parse times.

## Usage

### Command Line Arguments

```bash
search_in_archive.py --path <archive> --search <term> [options]
```

### Required Arguments

- `--path` : Path to the 7z archive.
- `--search` : Search term to look for in the archive. (Use quotes if the search term contains spaces)

### Optional Arguments

- `--password` : Password for the 7z archive.
- `--verbose` : Enable verbose mode to print search results to the console. (Default: OFF)
- `--buffer` : Keep results in buffer and write to file at the end. (Default: OFF)
- `--chunk_size` : Chunk size for reading (in bytes). (Default: 165536)
- `--line_update_interval` : Number of lines to process before printing progress. (Default: 100000000)
- `--chunk_update_interval` : Number of chunks to process before printing chunk progress. (Default: 100000)
- `--test` : Run in test mode, stop when output file reaches 10MB. [Use for estimating parse times]

### Performance Considerations

- **Verbose Mode:** Turning verbose mode on (`--verbose`) will significantly impact search speed, especially when there are many results. This is because each result is printed to the console, which slows down the processing.
  
- **Buffering Results:** Enabling buffering (`--buffer`) will also increase the search speed, as results are kept in memory and written to the file only at the end. However, using the buffer has drawbacks:
  - **Progress Updates:** When buffering is enabled, it's harder to track progress since results are not being written out in real-time. The `--line_update_interval` and `--chunk_update_interval` options can be used to get periodic updates.
  - **Data Loss Risk:** If the script is stopped early or if there is a crash, the results stored in the buffer may be lost since they haven't been written to the file yet.

### Test Mode (`--test`)

The `--test` option is designed to help you evaluate the performance of different configurations by limiting the output file size to 10MB. The script will run until this limit is reached and then stop, allowing you to measure the runtime for that particular configuration. 

This feature is especially useful for:
- **Gauging Search Speed:** By running the script with different settings (e.g., buffer on/off, various chunk sizes), you can determine which configuration provides the best performance.
- **System Stability:** Testing under controlled conditions to ensure that the script performs reliably before running a full search.

It is recommended to use the same keyword search across tests to get consistent performance metrics.

### Example

It is suggested to run with this command first to verify output and stability:

```bash
python search_in_archive.py --path archive.7z --search keyword --password SecretPassword --buffer --test
```

## Requirements

- Python 3.x
- `7z` installed and available in your system's PATH.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/search-in-7z-archive.git
   ```
2. Navigate to the project directory:
   ```bash
   cd search-in-7z-archive
   ```
3. ??

4. Run the script with the appropriate arguments.

```bash
PS X:\BeachData> python .\search_v2.py --path ABC202401.7z --search keyword --password https://password.io/ --test
2024-02-23 03:29:32 [INFO] Starting search in archive.
2024-02-23 03:29:32 [INFO] Search started at 2024-02-23 03:29:32.490296
2024-02-23 03:29:32 [INFO] Running command: H:\Program Files\7-Zip\7z.exe x -so -phttps://password.io/ ABC202401.7z
2024-02-23 03:29:41 [INFO] Test mode: Output file size reached 10MB. Stopping...
2024-02-23 03:29:46 [INFO] End of stderr stream reached.
2024-02-23 03:29:46 [INFO] Search complete. Finished at 2024-02-23 03:29:46.329095
2024-02-23 03:29:46 [INFO] Total run time: 0:00:13.838799
PS X:\BeachData>
```

## License

This project is license- see the [LICENSE](LICENSE) file for details.
