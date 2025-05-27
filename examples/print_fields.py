import argparse
from pathlib import Path

from vtk_scene.io import ReaderFactory


def main():
    parser = argparse.ArgumentParser("Print dataset fields")
    parser.add_argument("--data", help="file to load")
    args = parser.parse_known_args()[0]
    input_file = Path(args.data).resolve()
    if input_file.exists():
        ds = ReaderFactory.read(str(input_file))
        print("=" * 60)
        print("Dataset:", input_file)

        if len(ds.point_data):  # need to fix it in VTK
            print("=" * 60)
            print("Point Data")
            print("=" * 60)
            for name in ds.point_data:
                print(f" - {name}")

        if len(ds.cell_data):  # need to fix it in VTK
            print("=" * 60)
            print("Cell Data")
            print("=" * 60)
            for name in ds.cell_data:
                print(f" - {name}")

        if len(ds.field_data):  # need to fix it in VTK
            print("=" * 60)
            print("Field Data")
            print("=" * 60)
            for name in ds.field_data:
                print(f" - {name}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
