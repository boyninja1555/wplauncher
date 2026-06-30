import subprocess
import sys
import os
import json
import zipfile


class LauncherManifest:
    def __init__(self, version: int, main_class: str):
        self.version = version
        self.main_class = main_class

    @staticmethod
    def from_dict(data: dict) -> "LauncherManifest":
        return LauncherManifest(
            version=data.get("version", 0),
            main_class=data.get("main_class", ""),
        )


def java_command(
    args: list[str],
    capture_output: bool = False,
    text: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess | subprocess.CalledProcessError:
    result = subprocess.run(
        ["java", *args], capture_output=capture_output, text=text, check=check
    )

    return result


def java_version() -> int:
    try:
        output = java_command(["-version"], capture_output=True, text=True).stderr
        version_str = output.split('"')[1]
        major_version = int(version_str.split(".")[0])
        return major_version
    except Exception as ex:
        print(f"Error checking Java version! {ex}")
        return -1


def launch_command(
    manifest: LauncherManifest, version_directory: str, game_directory: str = "."
):
    try:
        classpath = os.pathsep.join(
            [
                os.path.join(version_directory, f"worldplate-{manifest.version}.jar"),
                os.path.join(version_directory, "libs", "*"),
            ]
        )

        java_command(
            [
                "--enable-native-access=ALL-UNNAMED",
                "-cp",
                classpath,
                manifest.main_class,
                game_directory,
            ]
        )

    except subprocess.CalledProcessError as ex:
        print(f"Error launching Worldplate! {ex.stderr}")


def parse_manifest(jar: str) -> LauncherManifest:
    with zipfile.ZipFile(jar, "r") as zip:
        with zip.open("launcher.json") as file:
            manifest = json.load(file)

    return LauncherManifest.from_dict(manifest)


def unbunle_versionpack(pack: str, version_directory: str):
    if not zipfile.is_zipfile(pack):
        print(
            f"{os.path.basename(pack)} is not a valid version pack! It cannot be unbundled."
        )
        sys.exit(1)

    import shutil

    shutil.rmtree(version_directory)

    with zipfile.ZipFile(pack, "r") as zip:
        zip.extractall(version_directory)

    os.remove(pack)


def main():
    if java_version() < 25:
        print("Java 25 or higher is required!")
        sys.exit(1)

    root = os.getcwd()
    version_pack = os.path.join(root, "wpversion.pack")
    version_directory = os.path.join(root, ".wpversion")
    game_directory = os.path.join(root, ".worldplate")
    jar = os.path.join(version_directory, "worldplate-1.jar")

    if os.path.isfile(version_pack):
        unbunle_versionpack(version_pack, version_directory)

    if not os.path.isfile(jar):
        print("Please ensure you have installed Worldplate correctly!")
        print(
            f"\tYou need to place your {os.path.basename(version_pack)} next to this launcher."
        )

        sys.exit(1)

    if not zipfile.is_zipfile(jar):
        print("Invalid Worldplate installation! It cannot be launched.")
        sys.exit(1)

    launch_command(parse_manifest(jar), version_directory, game_directory)


if __name__ == "__main__":
    main()
