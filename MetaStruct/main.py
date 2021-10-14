from MetaStruct.Objects.DesignSpace import DesignSpace
from MetaStruct.Objects.Lattices.Primitive import Primitive
from MetaStruct.Objects.Shapes.Cylinder import Cylinder


def main():
    # Execute code here
    ds = DesignSpace()
    shape = Cylinder(ds) / Primitive(ds)
    shape.previewModel()


if __name__ == '__main__':
    main()
