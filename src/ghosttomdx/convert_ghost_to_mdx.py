"""
A console script for ingesting a ghost export file,
and exporting mdx files for a nextjs static site.
"""
from argparse import ArgumentParser
import json
import os
import jsonschema
import pandas as pd
from packaging import version


def convert_ghost_export_to_mdx():
    """Run the conversion using parameters from the command line."""
    # Extract arguments from the command line interface, and make them human readable
    (import_file, export_json_schema_file, export_folder_path) = parse_arguments()
    import_file_json = import_json_file(import_file)
    export_json_schema = import_json_file(export_json_schema_file)
    try:
        jsonschema.validate(export_json_schema, import_file_json)
    except jsonschema.exceptions.ValidationError as err:
        print(err)
        raise Exception("The export file does not match the schema file.") from err
    ghost_db = import_file_json["db"][0]
    ghost_db_version = ghost_db["meta"]["version"]
    version_check(ghost_db_version)
    ghost_data = ghost_db["data"]
    (
        ghost_posts_and_pages,
        ghost_posts_meta,
        ghost_posts_tags,
        ghost_tags,
        ghost_users,
    ) = (
        ghost_data["posts"],
        ghost_data["posts_meta"],
        ghost_data["posts_tags"],
        ghost_data["tags"],
        ghost_data["users"],
    )
    df_tags = convert_tags(ghost_tags)
    df_users = convert_users(ghost_users)
    convert_posts_and_pages(
        export_folder_path,
        ghost_posts_and_pages,
        ghost_posts_meta,
        ghost_posts_tags,
        df_tags,
        df_users,
    )
    print("Script complete.")


def convert_tags(ghost_tags):
    df_tags, dict_tags = extract_tags(ghost_tags)
    set_tag_index_to_id(df_tags)
    return df_tags


def convert_users(ghost_users):
    df_users = extract_users(ghost_users)
    return df_users


def convert_posts_and_pages(
    export_folder_path,
    ghost_posts_and_pages,
    ghost_posts_meta,
    ghost_posts_tags,
    df_tags,
    df_users,
):
    ghost_posts_and_pages, ghost_posts_meta = apply_metadata_to_posts(
        ghost_posts_and_pages, ghost_posts_meta
    )

    ghost_pages, ghost_posts = (
        filter_type(ghost_posts_and_pages, "page"),
        filter_type(ghost_posts_and_pages, "post"),
    )
    convert_pages(export_folder_path, df_users, ghost_pages)
    convert_posts(export_folder_path, ghost_posts_tags, df_tags, df_users, ghost_posts)


def convert_pages(export_folder_path, df_users, ghost_pages):
    dict_pages = extract_pages(df_users, ghost_pages)
    dict_pages = remove_blank_fields(dict_pages)
    write_to_template(
        export_folder_path, dict_pages, "pages", "page_template.tpl", ".tsx"
    )


def write_to_template(
    export_folder_path,
    dict_pages_or_posts,
    folder_for_type,
    template_file_name,
    file_ext,
):
    template = read_template_file(export_folder_path, template_file_name)
    if not os.path.exists(f"{export_folder_path}/{folder_for_type}"):
        os.makedirs(f"{export_folder_path}/{folder_for_type}")
    # iterate over dictionary
    for data in dict_pages_or_posts:
        page_or_post_data = dict_pages_or_posts[data]
        string_to_write = token_replace_template(page_or_post_data, template)
        with open(
            f"{export_folder_path}/{folder_for_type}/" + data + file_ext, "w"
        ) as f:
            f.write(string_to_write)


def token_replace_template(dict_to_replace, template_string):
    for key, value in dict_to_replace.items():
        token = f"{{{{{key}}}}}"
        value = str(value)
        template_string = template_string.replace(token, value)
    return template_string


def read_template_file(export_folder_path, template_file_name):
    with open(f"{export_folder_path}{template_file_name}", "r") as file:
        template = file.read()
    return template


def convert_posts(export_folder_path, ghost_posts_tags, df_tags, df_users, ghost_posts):
    df_posts = apply_author_name(df_users, ghost_posts)
    dict_posts = apply_tags(ghost_posts_tags, df_tags, df_posts)
    dict_posts = remove_blank_fields(dict_posts)
    dict_posts = add_required_post_template_fields(dict_posts)
    write_to_template(
        export_folder_path, dict_posts, "posts", "post_template.tpl", ".mdx"
    )


def add_required_post_template_fields(dict_posts):
    required_fields = ["custom_excerpt", "title", "html"]
    for post in dict_posts:
        dict_posts[post]["slug"] = post
        dict_posts[post]["post_date"] = select_best_post_date(dict_posts[post])
        for field in required_fields:
            if field not in dict_posts[post]:
                dict_posts[post][field] = ""

    return dict_posts


def select_best_post_date(post_item):
    date = ""
    if "published_at" in post_item:
        date = post_item["published_at"]
    elif "created_at" in post_item:
        date = post_item["created_at"]
    elif "updated_at" in post_item:
        date = post_item["updated_at"]
    return date


def apply_tags(ghost_posts_tags, df_tags, df_posts):
    dict_posts = df_posts.to_dict(orient="index")
    for post in dict_posts:
        dict_posts[post]["tags"] = []
        for tag in ghost_posts_tags:
            if tag["post_id"] == dict_posts[post]["id"]:
                tag_id = tag["tag_id"]
                tag_name = df_tags.loc[tag_id]["name"]
                dict_posts[post]["tags"].append(tag_name)
    return dict_posts


def apply_author_name(df_users, ghost_posts):
    df_posts = pd.DataFrame(ghost_posts)
    df_posts.set_index("slug", inplace=True)
    df_posts.dropna(axis=1, how="all", inplace=True)
    df_posts["author_name"] = df_posts["author_id"].map(df_users["name"])
    df_posts.drop(columns=["mobiledoc"], inplace=True)
    df_posts = df_posts.where((pd.notnull(df_posts)), None)
    return df_posts


def remove_blank_fields(dict_post_or_page_data):
    for page_slug in dict_post_or_page_data:
        dict_post_or_page_data[page_slug] = {
            key: value
            for key, value in dict_post_or_page_data[page_slug].items()
            if value is not None
        }
        dict_post_or_page_data[page_slug] = {
            key: value
            for key, value in dict_post_or_page_data[page_slug].items()
            if value != ""
        }
    return dict_post_or_page_data


def convert_to_html(export_folder_path, dict_html, folder):
    if not os.path.exists(f"{export_folder_path}{folder}"):
        os.makedirs(f"{export_folder_path}{folder}")
    for htmlData in dict_html:
        if "html" in dict_html:
            html = dict_html[htmlData]["html"]
            with open(f"{export_folder_path}{folder}/" + htmlData + ".html", "w") as f:
                f.write(html)
            dict_html[htmlData].pop("html")
    return dict_html


def extract_pages(df_users, ghost_pages):
    df_pages = pd.DataFrame(
        ghost_pages,
        columns=[
            "title",
            "slug",
            "html",
            "feature_image",
            "featured",
            "page",
            "status",
            "locale",
            "visibility",
            "meta_title",
            "meta_description",
            "author_id",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
            "published_at",
            "published_by",
            "custom_excerpt",
            "codeinjection_head",
            "codeinjection_foot",
            "og_image",
            "og_title",
            "og_description",
            "twitter_image",
            "twitter_title",
            "twitter_description",
            "custom_template",
            "canonical_url",
            "url",
        ],
    )
    df_pages.set_index("slug", inplace=True)
    df_pages.dropna(axis=1, how="all", inplace=True)
    df_pages["author_name"] = df_pages["author_id"].map(df_users["name"])
    df_pages = df_pages.where((pd.notnull(df_pages)), None)
    df_pages.head()

    dict_pages = df_pages.to_dict(orient="index")
    return dict_pages


def filter_type(to_be_filtered, post_type):
    filter_result = [x for x in to_be_filtered if x["type"] == post_type]
    return filter_result


def apply_metadata_to_posts(ghost_posts_and_pages, ghost_posts_meta):
    df_posts_meta = pd.DataFrame(ghost_posts_meta)
    df_posts_meta.set_index("post_id", inplace=True)
    df_posts_meta.drop(columns=["id", "email_only"], inplace=True)
    df_posts_meta.dropna(axis=1, how="all", inplace=True)
    dict_cleaned_posts_meta = df_posts_meta.to_dict(orient="index")

    for post_id in dict_cleaned_posts_meta:
        dict_cleaned_posts_meta[post_id] = {
            key: value
            for key, value in dict_cleaned_posts_meta[post_id].items()
            if value is not None
        }
    for post in ghost_posts_and_pages:
        post_id = post["id"]
        if post_id in dict_cleaned_posts_meta:
            post.update(dict_cleaned_posts_meta[post_id])
    return ghost_posts_and_pages, ghost_posts_meta


def set_tag_index_to_id(df_tags):
    df_tags.set_index("id", inplace=True)
    dict_tags = df_tags.to_dict(orient="index")


def extract_users(ghost_users):
    df_users = pd.DataFrame(
        ghost_users,
        columns=[
            "id",
            "name",
            "slug",
            "email",
            "profile_image",
            "cover_image",
            "bio",
            "website",
            "location",
            "facebook",
            "twitter",
        ],
    )
    df_users.set_index("id", inplace=True)
    dict_users = df_users.to_dict(orient="index")
    return df_users


def extract_tags(ghost_tags):
    df_tags = pd.DataFrame(
        ghost_tags, columns=["id", "name", "slug", "description", "feature_image"]
    )
    df_tags.set_index("slug", inplace=True)
    dict_tags = df_tags.to_dict(orient="index")
    return df_tags, dict_tags


def clean_and_extract_settings(ghost_settings):
    ghost_settings_we_care_about = [
        "title",
        "description",
        "cover_image",
        "icon",
        "lang",
        "timezone",
        "codeinjection_head",
        "codeinjection_foot",
        "facebook",
        "twitter",
        "navigation",
        "secondary_navigation",
    ]

    df_settings = pd.DataFrame(ghost_settings, columns=["key", "value"])
    df_settings.set_index("key", inplace=True)
    df_settings_we_care_about = df_settings.loc[ghost_settings_we_care_about]
    settings_we_care_about = df_settings_we_care_about.to_dict()["value"]
    settings_we_care_about["navigation"] = json.loads(
        settings_we_care_about["navigation"]
    )
    settings_we_care_about["secondary_navigation"] = json.loads(
        settings_we_care_about["secondary_navigation"]
    )
    return settings_we_care_about


def parse_arguments():
    """Read in the arguments from the command line, and return them as a usable object.
    No keyword arguments required.
    Returns:
    arguments -- a python object with the command line arguments passed to the script
    """
    par = ArgumentParser()
    par.add_argument(
        "-f",
        "--import-file",
        type=str,
        default="data/export.json",
        help="Import filename",
    )
    par.add_argument(
        "-s",
        "--export-schema",
        type=str,
        default="data/ghost-4.37.0.schema",
        help="Ghost export schema filename",
    )
    par.add_argument(
        "-p",
        "--folder-path",
        type=str,
        default="data/",
        help="Path to folder for export",
    )
    arguments = par.parse_args()
    return arguments.import_file, arguments.export_schema, arguments.folder_path


def version_check(ghost_db_version):
    """Check that the ghost version is supported.
    Keyword arguments:
    ghost_version -- the version of ghost that the export file was created with
    """
    if version.parse(ghost_db_version) > version.parse("4.37.0"):
        print(
            "Ghost database version is greater than 4.37.0.  This script may not work."
        )
    elif version.parse(ghost_db_version) < version.parse("4.37.0"):
        print("Ghost database version is less than 4.37.0.  This script may not work.")
    elif version.parse(ghost_db_version) == version.parse("4.37.0"):
        print("Ghost database version is 4.37.0.  This script should work.")


def import_json_file(file_path):
    with open(file_path) as f:
        return json.load(f)


if __name__ == "__main__":
    convert_ghost_export_to_mdx()
