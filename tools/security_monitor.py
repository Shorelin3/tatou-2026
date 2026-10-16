import subprocess


def main():
    print("=" * 60)
    print("Tatou Security Monitor")
    print("Monitoring security events from the server...")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    command = [
        "docker",
        "compose",
        "-f",
        "docker-compose.yml",
        "-f",
        "docker-compose.local.yaml",
        "logs",
        "-f",
        "server",
    ]

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        for line in process.stdout:
            if (
                "SECURITY ALERT" in line
                or "Login failed:" in line
                or "Document access denied:" in line
                or "Server error:" in line
                or "RMAP authentication failed:" in line
            ):
                print(line, end="")

    except KeyboardInterrupt:
        print("\nSecurity monitoring stopped.")
        process.terminate()


if __name__ == "__main__":
    main()