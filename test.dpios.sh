#!/bin/bash
coverage run -m pytest tests/ $@
coverage report -m --omit=tests/*
