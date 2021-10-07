from Objects.DesignSpace import DesignSpace
from Objects.Lattices.Gyroid import Gyroid
from Objects.Lattices.BCC import BCC
from Objects.Shapes.Cuboid import Cuboid
from Objects.Booleans.Boolean import SmoothUnion
from Functions.Remap import remap


def lattice_slabs():

    skin_thicks = [1.0]
    vfs = [0.5]

    x_dim = 50
    y_dim = 30
    z_dim = 5

    ds = DesignSpace(x_resolution=350, y_resolution=210, z_resolution=70, x_bounds=[0, x_dim*2], y_bounds=[
                     0, y_dim*2], z_bounds=[0, z_dim*2])

    for vf_idx, vf in enumerate(vfs):

        for sk_idx, skin in enumerate(skin_thicks):

            volume = Cuboid(ds, x=x_dim, y=y_dim, z=z_dim,
                            xd=x_dim-0.1, yd=y_dim-0.1, zd=z_dim-0.1)

            lattice = Gyroid(ds, x=x_dim, y=y_dim, z=z_dim,
                             lx=5, ly=5, lz=5, vf=vf)

            #lattice.vf = remap(ds.x_grid, 0.2, 0.6)

            volume /= lattice

            skins = Cuboid(ds, x=x_dim, y=y_dim, z=skin/2, xd=x_dim, yd=y_dim, zd=skin/2) + \
                Cuboid(ds, x=x_dim, y=y_dim, z=z_dim*2-(skin/2),
                       xd=x_dim, yd=y_dim, zd=skin/2)

            volume += skins

            # volume.previewModel()

            volume.decimate_mesh(0.5)

            volume.save_mesh(f'demo_slab')

            # volume.save_tet_mesh(filename=f'slab_{int(vf*100)}_{skin}')


def lattice_coupons(vf=0.5, skin=1.0):

    ds = DesignSpace(resolution=100, x_bounds=[-5, 5],
                     y_bounds=[-5, 5], z_bounds=[-5, 5])

    lattice_volume = Cuboid(ds, xd=5, yd=5, zd=4.9)

    lattice = Gyroid(ds, lx=5, ly=5, lz=5, vf=vf)

    lattice_volume /= lattice

    skins = Cuboid(ds, z=(skin/2)-5, xd=5, yd=5, zd=skin/2) + \
        Cuboid(ds, z=5-(skin/2), xd=5, yd=5, zd=skin/2)

    lattice_volume += skins

    lattice_volume.findSurface()

    lattice_volume.decimate_mesh(0.5)

    lattice_volume.save_mesh('test_coupon')


def main():

    lattice_coupons()


if __name__ == "__main__":

    main()
