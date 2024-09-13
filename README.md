# Stash DeepDanbooru
Python script to tag images in stash with DeepDanbooru.

## Dependencies
To use the script, you need a python environment that can access DeepDanbooru and have the dependencies for DeepDanbooru installed.

```bash
# Clone DeepDanbooru's git somewhere
git clone git@github.com:KichangKim/DeepDanbooru.git

# Create & activate a python virtual environment somewhere you want
python3 -m venv .venv
source .venv/bin/activate

# Go to the DeepDanbooru directory and install it + it's dependencies within the virtual environment
cd DeepDanbooru
pip install -r requirements.txt
python setup.py install
```
Now the virtual enviornment should be ready to run tag_images.py

## Usage
Before you can use it the two files `update_tags.sh` and `run_deepdanbooru.sh` need to be modified with your stash information. To do this open up the .sh file and edit the export values with the values your stash instance uses.
|Environment Variable|Useage|Example Value|
|-|-|-|
|STASH_GRAPHQL|The graphql endpoint to talk to your stash instance.|`http://127.0.0.1:9999/graphql`|
|STASH_API_KEY|The API Key to authenticate with the graphql endpoint of your stash instance.|`eyJhbGciOiJIUzI1NiIsIn...`|
|STASH_TAGME_ID|A numerical id of the stash tag that the script searches images with to tag.|`213`|
|STASH_HAS_BEEN_TAGGED_ID|A numerical id of the stash tag that the script gives to the image after it has been tagged in replacement of the tagme tag.|`230`|
|STASH_TAG_GENERATED_ID|A numerical id of the stash tag that the script gives as parent tag to any tags it generates that are missing in stash.|`81`|
|STASH_FORMAT_UNSUPPORTED_ID|A numerical id of the stash tag gets assigned in replacement of tagme whenever an error occurs in trying to run DeepDanbooru on the image which happens with animated gifs for example.|`632`|
|DEEPDANBOORU_MODEL_PATH|The path to a DeepDanbooru model that is used in tagging the images.|`./model`|
|UPDATE_TAG_CACHE|If set to true it'll update the `relations.json` with the DeepDanbooru tags and the matching stash tag ids.|`true`|
|STASH_CREATE_TAGS|If set to true together with UPDATE_TAG_CACHE it'll create any DeepDanbooru tags in stash that it couldn't find in stash during matching.|`true`|


To update the tag relations between the deepbooru output and existing tags in your stash instance run `update_tags.sh` with the virtual environment activated. To start tagging images with DeepDanbooru run `run_deepdanbooru.sh` with the virtual enviornment activated.

## Known Issues
* Animated Gifs don't work (and when one gets encountered it currently doesn't remove it from the temp directory)
* An API request fail like when the dns fails to resolve for some reason makes the script crash so `run_deepdanbooru.sh` needs to manually be restarted