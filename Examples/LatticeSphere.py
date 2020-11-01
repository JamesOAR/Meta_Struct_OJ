from Objects.DesignSpace import DesignSpace
from Objects.Shapes.HollowSphere import HollowSphere
from Objects.Booleans.Union import Union
from Objects.Lattices.Gyroid import Gyroid


def latticedSphereExample(outerRad=2, outerSkinThickness=0.1, innerRad=1, innerSkinThickness=0.1):

    ds = DesignSpace(res=300)

    outerSkin = HollowSphere(designSpace=ds, r=outerRad, t=outerSkinThickness)

    latticeSection = HollowSphere(r=outerRad-outerSkinThickness,
                                  t=outerRad - outerSkinThickness - innerRad,
                                  designSpace=ds) / Gyroid(designSpace=ds)

    innerSkin = HollowSphere(r=innerRad, t=innerSkinThickness, designSpace=ds)

    s1 = Union(outerSkin, Union(latticeSection, innerSkin))

    s1.previewModel(clip='x')