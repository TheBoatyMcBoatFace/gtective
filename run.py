# run.py
from holmes import authenticate_and_get_service, list_files

def main():
    service = authenticate_and_get_service()

    if service:
        list_files(service)
    else:
        print("Failed to authenticate.")

if __name__ == "__main__":
    main()
