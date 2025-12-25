# Docker Setup Instructions
## Duane "the Rock" Reade - Pharmacy AI Agent

## Prerequisites

- Docker installed on your system
- OpenAI API key

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Set your API key as an environment variable:**
   ```bash
   export OPENAI_API_KEY=your-api-key-here
   ```

2. **Build and run:**
   ```bash
   docker-compose up --build
   ```

3. **Open your browser:**
   ```
   http://localhost:5000
   ```

4. **Stop the container:**
   ```bash
   docker-compose down
   ```

---

### Option 2: Using Docker Directly

1. **Build the image:**
   ```bash
   docker build -t pharmacy-agent .
   ```

2. **Run the container:**
   ```bash
   docker run -p 5000:5000 \
     -e OPENAI_API_KEY=your-api-key-here \
     pharmacy-agent
   ```

3. **Open your browser:**
   ```
   http://localhost:5000
   ```

4. **Stop the container:**
   ```bash
   docker ps  # Find container ID
   docker stop <container-id>
   ```

---

## What Happens on Startup

When the Docker container starts, it automatically:

1. Installs all Python dependencies
2. Initializes the SQLite database with:
   - 10 Knicks players as users
   - 5 medications with full details
   - Sample prescriptions
3. Adds 3 additional medications with known drug interactions
4. Starts the Flask web server on port 5000

---

## Accessing the Application

Once running, the application is available at:
- **Local machine:** http://localhost:5000
- **Network access:** http://your-ip-address:5000

---

## Troubleshooting

### Port 5000 already in use

If port 5000 is already taken, modify `docker-compose.yml`:

```yaml
ports:
  - "5001:5000"  # Change 5001 to any available port
```

Then access at http://localhost:5001

### API Key not working

Make sure you've set the environment variable:
```bash
echo $OPENAI_API_KEY  # Should show your key
```

If empty, set it:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Container won't start

Check logs:
```bash
docker-compose logs
```

Or for direct Docker:
```bash
docker logs <container-id>
```

---

## Development Mode

To run with live code updates (mount local directory):

```bash
docker run -p 5000:5000 \
  -e OPENAI_API_KEY=your-api-key-here \
  -v $(pwd):/app \
  pharmacy-agent
```

---

## Data Persistence

The database is recreated fresh each time the container starts. This ensures a clean state for testing.

If you want to persist the database between runs, use the volume mapping in docker-compose.yml (already configured).

---

## Cleanup

Remove container and image:
```bash
docker-compose down --rmi all
```

Or manually:
```bash
docker rm <container-id>
docker rmi pharmacy-agent
```

---

## Security Note

Never commit your `.env` file or hardcode API keys in the Dockerfile. Always pass the API key as an environment variable at runtime.
