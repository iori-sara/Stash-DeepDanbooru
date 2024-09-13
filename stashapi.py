import json
import requests

class StashInstance(object):
    def __init__(self, url, api_key = None):
        self.url = url
        self.api_key = api_key

    def perform_query(self, query):
        body = {"query": query}
        header_dict = {"Content-Type": "application/json"}
        if self.api_key:
            header_dict["ApiKey"] = self.api_key
        response = requests.post(self.url, headers=header_dict, json=body)

        # print(response)
        # print(response.text)
        return json.loads(response.text)

    def save_image(self, image_object, path):
        header_dict = {}
        if self.api_key:
            header_dict["ApiKey"] = self.api_key
        response = requests.get(image_object["paths"]["image"], headers=header_dict)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
        else:
            print("Couldn't get image [%d]" % response.status_code)

    def get_tag_name_from_id(self, id):
        response = self.perform_query("{ findTag(id: %d) { name } }" % id)
        return response["data"]["findTag"]["name"]

    def create_new_tag(self, parent_id, name):
        response = self.perform_query("""
mutation
{
  tagCreate(input: {
    name: "%s",
    parent_ids: [
      %d
    ]
  }) {
    id
    name
  }
}
        """ % (name.title(), parent_id))
        return response["data"]["tagCreate"]

    def update_image(self, id, new_tag_list):
        response = self.perform_query("""
mutation
{
  imageUpdate(input: {
    id: %d,
    tag_ids: %s
  }) {
    id
    tags {
      id
    }
  }
}
        """ % (id, str(new_tag_list)))
        # print(response)
        return response["data"]["imageUpdate"]

    def get_tags_from_name(self, name):
        response = self.perform_query("""
{
  findTags(filter: {q: "\\\"%s\\\"", per_page: -1})
  {
    tags
    {
      id
      name
      aliases
    }
  }
}""" % name)
        return response["data"]["findTags"]["tags"]

    def get_images_from_tag_id(self, id):
        response = self.perform_query("""
{
  findImages(image_filter: {tags: {value: [%d], modifier: INCLUDES_ALL}})
  {
    images
    {
      id
      # title
    }
  }
}""" % id)
        image_list = []
        for image in response["data"]["findImages"]["images"]:
            image_list.append(int(image["id"]))
        return image_list

    def get_image_info_from_id(self, id):
        response = self.perform_query("""
{
  findImage(id: %d)
  {
    title
    code
    urls
    date
    details
    organized
    created_at
    updated_at
    visual_files {
      __typename
      ... on ImageFile {
        path
      }
      ... on VideoFile {
        path
      }
    }
    paths {
      image
    }
    tags {
      id
    }
  }
}""" % id)
        return response["data"]["findImage"]