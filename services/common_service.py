def get_application_version():
    application_version = ""
    version_file = open('version.md', 'r')
    line = version_file.readline()
    line = line.strip()
    application_version = line
    version_file.close()
    return application_version