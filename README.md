# Tatou PDF Watermarking platform
A web platform for pdf watermarking

## Table of contents
- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Running the Project](#running-the-project)
- [Running Tests](#running-tests)
  - [Unit Tests](#unit-tests)
  - [API Tests](#api-tests)
  - [Coverage Analysis](#coverage-analysis)
- [Additional Testing](#additional-testing)
  - [Mutation Testing](#mutation-testing)
  - [Fuzz Testing](#fuzz-testing)
  - [Regression Testing](#regression-testing)
  - [RMAP Testing](#rmap-testing)
  - [Security Monitoring Testing](#security-monitoring-testing)
- [Deployment](#deployment)
  - [Local Development with Docker](#local-development-with-docker)
  - [Deployment Commands](#deployment-commands)
  - [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
  - [User Endpoints](#user-endpoints)
  - [Document and Watermarking Endpoints](#document-and-watermarking-endpoints)
  - [RMAP Endpoints](#rmap-endpoints)
- [Contributors](#contributors)
- [License](#license)

---

## Project overview
The project uses:
- **Backend:** Python / Flask
- **Database:** MariaDB
- **Deployment:** Docker and Docker Compose
- **Testing:** Pytest

---

## Prerequisites

Following software is required:
- Python 3.11 or later
- Docker
- Docker compose
- Git

---
## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Shorelin3/tatou-2026.git
cd tatou-2026
```

### 2. Set up the Python environment
Go to the server directory:

```bash
cd server
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```
Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

---

## Running the Project

From the root directory of the project, build and start the application:

```bash
docker compose up --build -d
```

Check that the containers are running:

```bash
docker compose ps
```

The application is available at:

```text
http://localhost:5000
```

---

## Running tests

### Unit tests

Go to the server directory and activate the virtual environment:

```bash
cd server
source .venv/bin/activate
```

Run the pytest test suite, excluding the Atheris fuzzing harnesses:

```bash
python -m pytest
  --ignore=test/test_fuzz_atheris_a01.py \
  --ignore=test/test_fuzz_atheris_a02.py \
  --ignore=test/test_fuzz_atheris_a03.py \
  --ignore=test/test_fuzz_atheris_extended_a02.py \
  -v
```

To run a specific test file: 

```bash
python -m pytest test/<test_filename>.py -v
```

### API tests
API tests are included in the test suite.

To run a specific API test file, replace `<test_filename>` with the name of the test file:

```bash
python -m pytest test/<test_filename>.py -v
```

Additional API tests are available in the `server/test/` directory.

### Coverage Analysis

Test coverage is measured using pytest-cov. 

To run the coverage analysis from the project root directory: 

```bash
DB_HOST=127.0.0.1 \
DB_NAME=tatou_test \
DB_PASSWORD="$(docker compose exec -T server printenv DB_PASSWORD | tr -d '\r\n')" \
STORAGE_DIR="$PWD/storage_test" \
python -m pytest server/test \
 --ignore=server/test/test_fuzz_atheris_a01.py \
 --ignore=server/test/test_fuzz_atheris_a02.py \
 --ignore=server/test/test_fuzz_atheris_a03.py \
 --ignore=server/test/test_fuzz_atheris_extended_a02.py \
 --cov=server/src \
 --cov-branch \
 --cov-report=term-missing \
 --cov-report=html:coverage_html \
 -v
```

**Important:** The coverage tests use a separate database (`tatou_test`) and storage directory (`storage_test`) to avoid modifying the application's regular data. 
See [Test Database Setup](#test-database-setup) for instructions.

The generated HTML coverage report is available in `coverage_html`/.
A copy is available in `artifacts/common/coverage_html/`.

### Test Database Setup

Start the Docker containers:

```bash
docker compose up -d
```

Create the test database, import the Tatou schema, and grant access to the configured database user:

```bash
docker compose exec -T db sh -c '
mariadb -u root -p"$MARIADB_ROOT_PASSWORD" <<SQL
CREATE DATABASE IF NOT EXISTS tatou_test;
GRANT ALL PRIVILEGES ON tatou_test.* TO '"'"'$MARIADB_USER'"'"'@'"'"'%'"'"';
SQL
'
```

Import the Tatou database schema into the test database:

```bash
sed 's/`tatou`/`tatou_test`/g' db/tatou.sql | \
docker compose exec -T db sh -c 'mariadb -u root -p"$MARIADB_ROOT_PASSWORD"'
```

The coverage tests can then be run using the command in the [Coverage Analysis section](#coverage-analysis)

---

## Additional testing

In addition to the regular unit and API tests, the project includes additional testing methods developed as part of the Phase II specializations.

### Mutation Testing

Mutation testing artifacts are available in:

```text
artifacts/melissa/mutation-testing/
```

The project also contains a dedicated mutation test:

```text
server/test/test_add_after_eof_mutation.py
```

### Fuzz Testing

Atheris fuzzing harnesses are executed separately and should be excluded from standard pytest test collection. 

The fuzzing scripts are located in: 

```text
server/test/test_fuzz_atheris_a01.py
server/test/test_fuzz_atheris_a02.py
server/test/test_fuzz_atheris_a03.py
server/test/test_fuzz_atheris_extended_a02.py
```

Detailed fuzzing documentation is available in
[Specialization A Artifacts](artifacts/joel/README.md).

### Regression Testing

Regression tests are included to verify that previously tested functionality continues to work after changes to the application.

The regression tests are located in:

```text
server/test/test_regression_a01.py
server/test/test_regression_a02.py
server/test/test_regression_a03.py
```

### RMAP Testing

The project includes tests for the RMAP integration, including API-level and end-to-end testing.

```text
server/test/test_rmap_api.py
server/test/test_rmap_e2e.py
```

### Security Monitoring Testing

```text
server/test/test_security_monitoring.py
```

Additional Operational Security testing and documentation can be found in:

```text
artifacts/ebba/
```

---

## Deployment

### Local Development with Docker

The application can be deployed locally using Docker Compose.

```bash
# From the root directory of the project

# 1. Create the environment file
cp sample.env .env

# 2. Edit .env and configure the required passwords and variables
# Required variables:
#   - MARIADB_ROOT_PASSWORD
#   - MARIADB_USER
#   - MARIADB_PASSWORD
#   - FLAG_2 
nano .env  

# 3. Build and start the containers
docker compose up --build -d

# 4. Check that the containers are running
docker compose ps

# 5. Monitor logs in real time
docker compose logs -f

# 6. Open the web interface
# Navigate to http://127.0.0.1:5000 in your browser
```

The Docker Compose deployment starts three services:

- `server` - Flask application on port `5000`
- `db` - MariaDB 11.4 database
- `phpmyadmin` - Database administration interface on `127.0.0.1:8080`

The MariaDB service is available locally on `127.0.0.1:3306`.

### Deployment Commands

```bash
# Start the containers
docker compose up -d

# Build and start the containers
docker compose up --build -d

# Stop all containers
docker compose down

# Rebuild and restart
docker compose down
docker compose up --build -d

# Check container status
docker compose ps

# View server logs
docker compose logs server

# View database logs
docker compose logs db

# Follow all logs in real time
docker compose logs -f

# Access the server container
docker compose exec server bash
```

### Environment Variables

Key environment variables in `.env`:

```bash
MARIADB_ROOT_PASSWORD=<your_root_password>
MARIADB_USER=<database_user>
MARIADB_PASSWORD=<database_password>
FLAG_2=<your_flag_value>
RMAP_WATERMARK_KEY=<watermark_key>
RMAP_WATERMARK_METHOD=<watermark_method>
RMAP_KEY_PASSPHRASE=<key_passphrase>
```

Real passwords, flags, and other secrets should only be stored in `.env` and should not be committed to the repository.

---

## Project structure
```text
tatou-2026/
├── artifacts/
│   ├── common/                              # Shared Phase II artifacts
│   │   ├── specification_test_mapping.md    # Mapping between specifications and tests
│   │   └── coverage_html/                   # Test coverage artifacts
│   │
│   ├── ebba/                                # Operational Security specialization
│   │   ├── README.md
│   │   ├── threat_model.md                  # Threat model and risk assessment
│   │   ├── account_attackTree.svg           # Account attack tree
│   │   ├── sensitive_info_attacktree.svg    # Sensitive information attack tree
│   │   ├── unauthorized_document_attackTree.svg
│   │   ├── observation_points.md            # Security observation points
│   │   ├── detection_rules.md               # Detection rules
│   │   ├── monitoring.md                    # Monitoring documentation
│   │   ├── testing.md                       # Operational security testing
│   │   ├── incident_journal_template.md     # Incident journal
│   │   ├── incident_report_flag1.md         # Flag incident report
│   │   ├── incident_report_uploaded_files.md
│   │   └── specializationD_report.md        # Operational Security report
│   │
│   │
│   ├── joel/                                # Phase II specialization
│   │   ├── README.md
│   │   ├── bugs_discovered.md
│   │   ├── fuzzer_configurations.md
│   │   ├── fuzzing_results.md                
│   │   └── non_regression_tests.md
│   │
│   │
│   └── melissa/                             # Phase II specialization 
│       └── mutation-testing/
│
├── db/
│   └── tatou.sql                            # Database initialization
│
├── scripts/
│   └── backup.sh                            # Backup script
│
├── Security-Requirements/
│   └── securityRequirements.md              # Security requirements
│
├── server/
│   ├── src/                                 # Application source code
│   │   ├── server.py                        # Main Flask application
│   │   ├── security_monitoring.py           # Security monitoring implementation
│   │   ├── watermarking_method.py           # Watermarking interface
│   │   ├── watermarking_utils.py            # Watermarking utilities
│   │   ├── watermarking_cli.py              # Watermarking CLI
│   │   ├── add_after_eof.py                 # EOF watermarking
│   │   ├── duplicate_watermark.py           # Duplicate watermarking
│   │   ├── microdot_watermark.py            # Microdot watermarking
│   │   ├── visible_hmac.py                  # Visible HMAC watermarking
│   │   └── unsafe_bash_bridge_append_eof.py
│   │
│   ├── test/                                # Automated test suite
│   │   ├── test_api.py                      # API tests
│   │   ├── test_security_monitoring.py      # Security monitoring tests
│   │   ├── test_rmap_api.py                 # RMAP API tests
│   │   ├── test_rmap_e2e.py                 # RMAP end-to-end tests
│   │   ├── test_regression_a01.py           # Regression tests
│   │   ├── test_regression_a02.py
│   │   ├── test_regression_a03.py
│   │   ├── test_fuzz_atheris_a01.py         # Fuzz tests
│   │   ├── test_fuzz_atheris_a02.py
│   │   ├── test_fuzz_atheris_a03.py
│   │   └── test_watermarking_all_methods.py
│   │
│   ├── keys/                                # RMAP keys
│   ├── API.md                               # API documentation
│   ├── Dockerfile                           # Server Docker image
│   ├── entrypoint.sh                        # Container startup script
│   └── pyproject.toml                       # Python dependencies and configuration
│
├── tools/
│   └── security_monitor.py                  # Security monitoring tool
│
├── docker-compose.yml                       # Docker Compose deployment
├── docker-compose.local.yaml                # Local Docker configuration
├── Platform_specifications.md               # Platform specifications
├── sample.env                               # Example environment configuration
├── LICENSE
└── README.md
```

The main application implementation is located in `server/src/`, with automated tests in `server/test/`. Phase II documentation and specialization-specific artifacts are organized under `artifacts/`.

---

## API documentation
Detailed API specifications are available in `server/API.md`.

### User Endpoints

- `POST /api/create-user` - Create a new user account
- `POST /api/login` - Authenticate a user
- `GET /api/healthz` - Check server health

### Document and Watermarking Endpoints

- `POST /api/upload-document` - Upload a PDF document
- `GET /api/list-documents` - List the authenticated user's documents
- `GET /api/get-document/<document_id>` - Retrieve a specific document
- `DELETE /api/delete-document/<document_id>` - Delete a document
- `GET /api/list-versions/<document_id>` - List watermarked versions of a document
- `GET /api/list-all-versions` - List versions of all documents
- `GET /api/get-watermarking-methods` - List available watermarking methods
- `POST /api/create-watermark/<document_id>` - Create a watermarked version of a document
- `POST /api/read-watermark/<document_id>` - Read watermark information from a document
- `GET /api/get-version/<link>` - Retrieve a specific watermarked document version

### RMAP Endpoints

- `POST /api/rmap-initiate` - Initiate RMAP communication
- `POST /api/rmap-get-link` - Complete the RMAP exchange and retrieve a document link

---
## Contributors
**Group 15**
- Ebba Arrhenius Winblad
- Joel Oskarsson
- Melissa Zaade

---
## License
This project is licensed under the terms specified in the `LICENSE` file.

---