
.PHONY: setup data

setup:
	uv venv
	uv pip install -r requirements.txt

data:
	uv run python src/setup/data_prep.py

# make train:
# 	python src/train/train.py

# make score:
# 	python src/score/score.py

# make deploy:
# 	python src/deploy/deploy.py

# make retrain:
# 	python src/retrain/retrain.py

# make pipeline:
# 	python src/pipeline/pipeline.py

# make all:
# 	make setup
# 	make data
# 	make train
# 	make score
# 	make deploy
# 	make retrain
# 	make pipeline