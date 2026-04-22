"""Tests for Dockerfile generation in server_generator."""

from __future__ import annotations

import os
import tempfile

from src.query.server_generator import generate_server


class TestDockerfileGeneration:
    """Verify generate_server produces a valid Dockerfile for each framework."""

    def test_flask_dockerfile_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("flask", tmp, "CUSTOMERS")
            dockerfile = os.path.join(tmp, "Dockerfile")
            assert os.path.isfile(dockerfile)

    def test_fastapi_dockerfile_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("fastapi", tmp, "CUSTOMERS")
            dockerfile = os.path.join(tmp, "Dockerfile")
            assert os.path.isfile(dockerfile)

    def test_flask_dockerfile_uses_python_311_slim(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("flask", tmp, "CUSTOMERS")
            content = open(os.path.join(tmp, "Dockerfile")).read()
            assert "FROM python:3.11-slim" in content

    def test_flask_dockerfile_installs_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("flask", tmp, "CUSTOMERS")
            content = open(os.path.join(tmp, "Dockerfile")).read()
            assert "COPY requirements.txt" in content
            assert "pip install" in content
            assert "-r requirements.txt" in content

    def test_flask_dockerfile_copies_app_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("flask", tmp, "CUSTOMERS")
            content = open(os.path.join(tmp, "Dockerfile")).read()
            assert "COPY . ." in content

    def test_flask_dockerfile_exposes_port_5000(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("flask", tmp, "CUSTOMERS")
            content = open(os.path.join(tmp, "Dockerfile")).read()
            assert "EXPOSE 5000" in content

    def test_flask_dockerfile_sets_cmd(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("flask", tmp, "CUSTOMERS")
            content = open(os.path.join(tmp, "Dockerfile")).read()
            assert "CMD" in content
            assert "app.py" in content

    def test_fastapi_dockerfile_uses_python_311_slim(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("fastapi", tmp, "CUSTOMERS")
            content = open(os.path.join(tmp, "Dockerfile")).read()
            assert "FROM python:3.11-slim" in content

    def test_fastapi_dockerfile_exposes_port_8000(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("fastapi", tmp, "CUSTOMERS")
            content = open(os.path.join(tmp, "Dockerfile")).read()
            assert "EXPOSE 8000" in content

    def test_fastapi_dockerfile_sets_uvicorn_cmd(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_server("fastapi", tmp, "CUSTOMERS")
            content = open(os.path.join(tmp, "Dockerfile")).read()
            assert "CMD" in content
            assert "uvicorn" in content
            assert "8000" in content

    def test_all_three_files_generated(self):
        """generate_server produces app.py, requirements.txt, and Dockerfile."""
        for framework in ("flask", "fastapi"):
            with tempfile.TemporaryDirectory() as tmp:
                generate_server(framework, tmp, "TEST")
                assert os.path.isfile(os.path.join(tmp, "app.py"))
                assert os.path.isfile(os.path.join(tmp, "requirements.txt"))
                assert os.path.isfile(os.path.join(tmp, "Dockerfile"))
