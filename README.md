# NaFi

NaFi is a tool designed to improve data security through file randomization. By systematically changing the structure and naming of files, NaFi protects sensitive information from unauthorized access.

---

## Requirements

Make sure you have installed:

- **Python 3.10** or later
- **pip** (Python Package Installer)

---

## How to Run the Application

Follow these steps to run the NaFi application:

### 1. Install Dependencies

Run the following command to install all required dependencies:

```bash
pip install -r requirements.txt
```

### 2. Create `.env` File

In the `NaFi` folder, create a `.env` file with the following content:

```
NAS_IP=
NAS_SSH_PORT=
UPLOAD_FOLDER=static/uploads
RESULT_FOLDER=static/processed
```

Fill in the appropriate values for `NAS_IP` and `NAS_SSH_PORT`.

### 3. Start the Application

Use the following command to start the application in the background using `nohup`:

```bash
nohup python3.10 NaFi.py &
```

### 4. Access the Application

Open your browser and access the application via the configured IP address. For example:

```
http://<IP-ADDRESS>:<PORT>
```

Replace `<IP-ADDRESS>` and `<PORT>` with the appropriate IP address and port.

---

## Additional Notes

- If you need to stop the application running in the background, use the following commands to locate and terminate the process:
  
  **Find PID:**
  ```bash
  ps aux | grep NaFi.py
  ```
  
  **Terminate the Process:**
  ```bash
  kill <PID>
  ```
  Replace `<PID>` with the process ID found in the previous step.

- Ensure that the port being used does not conflict with other services.

---

## Support

If you encounter any issues while running this application, please contact the development team or open an issue in the repository.

---

**Happy using NaFi!** 🚀
