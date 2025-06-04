#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "vtk==9.5.0rc2",
#     "trame>=3.10",
#     "trame-vtk",
#     "vtk-scene",
# ]
# [[tool.uv.index]]
# url = "https://wheels.vtk.org"
#
# [tool.uv.sources]
# vtk-scene = { url = "https://github.com/Kitware/vtk-scene/releases/download/v0.1.3/vtk_scene-0.1.3-py3-none-any.whl" }
# ///

# -----------------------------------------------------------------------------
# From numpy to Python
# Copyright (2017) Nicolas P. Rougier - BSD license
# More information at https://github.com/rougier/numpy-book
# https://www.labri.fr/perso/nrougier/from-python-to-numpy/code/gray_scott.py
# Parameters from http://www.aliensaint.com/uo/java/rd
# Adapted for vedo by Marco Musy (2020)
# => https://github.com/marcomusy/vedo/blob/master/examples/simulations/grayscott.py
# Adapted for trame & vtk-scene by Sebastien Jourdain (2025)
# -----------------------------------------------------------------------------
"""Grey-Scott reaction-diffusion system"""

import asyncio

import numpy as np

# VTK
import vtk

# GUI
from trame.app import TrameApp
from trame.decorators import change
from trame.ui.html import DivLayout
from trame.widgets import client, html
from trame.widgets import vtk as vtkw

from vtk_scene import RenderView

# ---------------------------------------------------------------
n = 200  # grid subdivisions
anim_speed = 0.01  # number of second to wait before next step
# ---------------------------------------------------------------
OPTIONS = {
    # name: (Du, Dv, F, k),
    "Bacteria 1": (0.16, 0.08, 0.035, 0.065),
    "Bacteria 2": (0.14, 0.06, 0.035, 0.065),
    "Coral": (0.16, 0.08, 0.060, 0.062),
    "Fingerprint": (0.19, 0.05, 0.060, 0.062),
    "Spirals": (0.10, 0.10, 0.018, 0.050),
    "Spirals Dense": (0.12, 0.08, 0.020, 0.050),
    "Spirals Fast": (0.10, 0.16, 0.020, 0.050),
    "Unstable": (0.16, 0.08, 0.020, 0.055),
    "Worms 1": (0.16, 0.08, 0.050, 0.065),
    "Worms 2": (0.16, 0.08, 0.054, 0.063),
    "Zebrafish": (0.16, 0.08, 0.035, 0.060),
}
# ---------------------------------------------------------------


class VizApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)
        self._setup_vtk()
        self._build_ui()

        # Auto start anitmation
        self.ctrl.on_client_connected.add_task(self._animate)

    def _setup_vtk(self):
        # VTK data model
        x = np.linspace(0, 1, n + 2)
        y = np.linspace(0, 1, n + 2)
        points = np.stack([v.ravel() for v in np.meshgrid(x, y, [0])], axis=1)
        self.grd = vtk.vtkStructuredGrid(
            dimensions=(n + 2, n + 2, 1),
            points=points,
        )

        # VTK Scene part
        self.view = RenderView()
        self.representation = self.view.create_representation(self.grd, type="Geometry")
        self.view.reset_camera()

    @change("model")
    def _on_model_change(self, model, **_):
        Z = np.zeros((n + 2, n + 2), [("U", np.double), ("V", np.double)])
        U, V = Z["U"], Z["V"]
        u, v = U[1:-1, 1:-1], V[1:-1, 1:-1]

        r = 20
        u[...] = 1.0
        U[n // 2 - r : n // 2 + r, n // 2 - r : n // 2 + r] = 0.50
        V[n // 2 - r : n // 2 + r, n // 2 - r : n // 2 + r] = 0.25
        u += 0.05 * np.random.uniform(-1, 1, (n, n))
        v += 0.05 * np.random.uniform(-1, 1, (n, n))

        # Update self
        self.U = U
        self.V = V
        self.u = u
        self.v = v
        self.Du, self.Dv, self.F, self.k = OPTIONS[model]
        self._update_data()

        # Display new data
        self.representation.update()
        self.ctx.vtk_view.update()

    def _update_data(self):
        for _ in range(25):
            Lu = (
                self.U[0:-2, 1:-1]
                + self.U[1:-1, 0:-2]
                - 4 * self.U[1:-1, 1:-1]
                + self.U[1:-1, 2:]
                + self.U[2:, 1:-1]
            )
            Lv = (
                self.V[0:-2, 1:-1]
                + self.V[1:-1, 0:-2]
                - 4 * self.V[1:-1, 1:-1]
                + self.V[1:-1, 2:]
                + self.V[2:, 1:-1]
            )
            uvv = self.u * self.v * self.v
            self.u += self.Du * Lu - uvv + self.F * (1 - self.u)
            self.v += self.Dv * Lv + uvv - (self.F + self.k) * self.v

        # VTK data model
        self.grd.point_data["escals"] = self.V.ravel()

        # VTK Scene
        self.representation.color_by("escals")
        self.representation.update()

    async def _animate(self, **_):
        while True:
            await asyncio.sleep(anim_speed)
            self._update_data()
            self.representation.update()
            self.ctx.vtk_view.update()

    def _build_ui(self):
        with DivLayout(self.server) as self.ui:
            # Full Screen
            client.Style("body{margin:0}")
            self.ui.root.style = "height: 100vh;"

            # Model selector
            with html.Select(
                style="position:absolute;top:1rem;right:1rem;z-index:1;",
                v_model=("model", "Zebrafish"),
            ):
                for name in OPTIONS:
                    html.Option(name, value=name)

            # VTK view
            vtkw.VtkRemoteView(
                self.view.render_window,
                interactive_ratio=1,
                ctx_name="vtk_view",
            )


def main():
    app = VizApp()
    app.server.start()


if __name__ == "__main__":
    main()
