#!/usr/bin/python

import stashapi

import os
import time
import json
import subprocess
from termcolor import colored
import deepdanbooru

API_KEY = os.environ["STASH_API_KEY"]

TAG_ID = int(os.environ["STASH_TAGME_ID"])
GENERATED_TAG_ID = int(os.environ["STASH_TAG_GENERATED_ID"])
HAS_BEEN_TAGGED_ID = int(os.environ["STASH_HAS_BEEN_TAGGED_ID"])
FORMAT_UNSUPPORTED_ID = int(os.environ["STASH_FORMAT_UNSUPPORTED_ID"])
TEMP_DIR = "/dev/shm/stash_image/"
PROJECT_PATH = os.environ["DEEPDANBOORU_MODEL_PATH"]

class AITagger(object):
    def __init__(self, project_path, allow_gpu):
        compile_model = None

        if not allow_gpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

        self.model = deepdanbooru.project.load_model_from_project(
            project_path, compile_model=compile_model
        )

        self.tags = deepdanbooru.project.load_tags_from_project(project_path)

    def evaluate(self, image_path, threshold = 0.7):
        tags = []
        for tag, score in deepdanbooru.commands.evaluate_image(image_path, self.model, self.tags, threshold):
            tags.append(tag.strip().lower().replace('_', ' '))

        return tags

def main():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    ai_tagger = AITagger(PROJECT_PATH, True)

    stash = stashapi.StashInstance(os.environ["STASH_GRAPHQL"], API_KEY)

    if "UPDATE_TAG_CACHE" in os.environ:
        if os.environ["UPDATE_TAG_CACHE"].lower() == "true":
            update_tag_cache(stash, GENERATED_TAG_ID)
            return

    print("Generated tag [%s]" % stash.get_tag_name_from_id(GENERATED_TAG_ID))

    print("Looking for images with tag %d" % TAG_ID)
    tag_name = stash.get_tag_name_from_id(TAG_ID)
    print("Tag name [%s]" % tag_name)
    print("Image IDs to process:")
    image_list = stash.get_images_from_tag_id(TAG_ID)
    print(image_list)

    while len(image_list) > 0:
        for imageid in image_list:
            start_time = time.time()
            tag_image(stash, ai_tagger,  imageid, TAG_ID, HAS_BEEN_TAGGED_ID, FORMAT_UNSUPPORTED_ID)
            end_time = time.time()
            time_elapsed = end_time - start_time
            print(colored("Time elapsed: %f" % time_elapsed, "blue"))

        print("Image IDs to process:")
        image_list = stash.get_images_from_tag_id(TAG_ID)

def update_tag_cache(stash, parent_id):
    relations = get_tag_id_relations(stash, PROJECT_PATH + "/tags.txt", parent_id)
    save_tag_id_relations(relations)

def tag_image(stash, ai_tagger, imageid, tag_id, has_been_tagged_id, format_unsupported_id):
    print("Image info:")
    image_info = stash.get_image_info_from_id(imageid)
    print(image_info)
    existing_tags = []
    for existing_tag in image_info["tags"]:
        existing_tag_id = int(existing_tag["id"])
        if existing_tag_id != tag_id:
            existing_tags.append(existing_tag_id)

    print("Image URL: %s" % image_info["paths"]["image"])

    try:
        temp_file = get_temp_filename_from_image_info(image_info)

        stash.save_image(image_info, temp_file)
        print("Temp image saved as [%s]" % temp_file)

        relations = load_tag_id_relations()
        image_deepbooru_tags = run_deepbooru(ai_tagger, temp_file)
        os.remove(temp_file)

        for tag in image_deepbooru_tags:
            if tag in relations.keys():
                exists_str = ""
                if relations[tag] in existing_tags:
                    exists_str = colored("Already on Image", "blue")
                else:
                    existing_tags.append(relations[tag])
                print(colored("Matched", "green"), "[%s](%d)" % (tag, relations[tag]), exists_str)
            else:
                print(colored("Skipping", "yellow"), "[%s]" % (tag))

        if has_been_tagged_id not in existing_tags:
            existing_tags.append(has_been_tagged_id)
    except Exception as e:
        print(e)
        existing_tags.append(format_unsupported_id)

    print(existing_tags)
    stash.update_image(imageid, existing_tags)

def run_deepbooru(ai_tagger, image_path):
    tags = ai_tagger.evaluate(image_path)
    return tags

def load_tag_id_relations(fname = "./relations.json"):
    rel_file = open(fname, "r")
    relations = json.loads(rel_file.read())
    rel_file.close()
    return relations

def save_tag_id_relations(relations, fname = "./relations.json"):
    rel_file = open(fname, "w")
    rel_file.write(json.dumps(relations))
    rel_file.close()

def get_tag_id_relations(stash, taglist, parent_id):
    print("Loading taglist")
    tagfile = open(taglist, 'r')
    tags = tagfile.readlines()
    tagfile.close()
    stripped_tags = []

    print("Stripping Tags")
    for tag in tags:
        stripped_tags.append(tag.strip().lower().replace('_', ' '))

    print("Tags:")
    matched_tags = {}
    to_create_tags = []
    skipped_tags = []
    errored = 0
    for tag in stripped_tags:
        try:
            stash_tags = stash.get_tags_from_name(tag)
            matched_stash_tag = None
            for stag in stash_tags:
                if stag["name"].lower().replace('_', ' ') == tag:
                    matched_stash_tag = stag
                    break
                else:
                    for alias in stag["aliases"]:
                        if alias.lower().replace('_', ' ') == tag:
                            matched_stash_tag = stag
                            break
                    if matched_stash_tag:
                        break
            if matched_stash_tag:
                print(colored("Matched", "green"), "[%s] with [%s](%d)" % (tag, matched_stash_tag["name"], int(matched_stash_tag["id"])))
                matched_tags[tag] = int(matched_stash_tag["id"])
            else:
                to_create_tags.append(tag)
        except Exception as e:
            print(colored("Error", "red"), "getting [%s] from stash [%s]" % (tag, str(e)))
            errored += 1

    created_count = 0

    if "STASH_CREATE_TAGS" in os.environ:
        if os.environ["STASH_CREATE_TAGS"].lower() == "true":
            for tag in to_create_tags:
                # replace all special characters with a letter and then check if it only contains alphabet characters since i wanted to filter out tags like \o/
                if tag.replace(' ', 'a').replace('-', 'a').replace('\'', 'a').replace('(', 'a').replace(')', 'a').isalpha():
                    create_new_tag = stash.create_new_tag(parent_id, tag)
                    matched_tags[tag] = int(create_new_tag['id'])
                    print(colored("Created", "cyan"), "[%s](%d)" % (create_new_tag["name"], int(create_new_tag["id"])))
                    created_count += 1
                else:
                    skipped_tags.append(tag)
        else:
            skipped_tags = to_create_tags
    else:
        skipped_tags = to_create_tags

    print("Done matching,", colored("Matched: %d" % len(matched_tags), "green"), colored("Created: %d" % created_count, "blue"), colored("Skipped: %d" % len(skipped_tags), "yellow"), colored("Errored: %d" % errored, "red"))

    skipped_file = open("./skipped.txt", "w")
    for tag in skipped_tags:
        skipped_file.write(tag + "\n")
    skipped_file.close()

    return matched_tags


def get_temp_filename_from_image_info(image_info):
    tmp_dir = TEMP_DIR
    if not tmp_dir.endswith('/'):
        tmp_dir.append('/')
    fname = image_info["visual_files"][0]["path"]
    if image_info["visual_files"][0]["__typename"] == "VideoFile":
        raise Exception("Video file requested")
    return tmp_dir + fname[fname.rfind('/')+1:]

if __name__=="__main__":
    main()