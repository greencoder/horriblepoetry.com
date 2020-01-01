import argparse
import arrow
import glob
import itertools
import jinja2
import markdown
import pathlib
import shutil

from config import Config
from config import Section
from config import Post

def parse_metadata(metadata_string):
    """ Parses the metadata headers """
    metadata = {}

    for line in metadata_string.split('\n'):
        tag, contents = line.split(':', 1)
        tag = tag.lower()

        if tag.endswith('s'):
            metadata[tag] = [c.strip() for c in contents.split(',')]
        else:
            metadata[tag] = contents.strip()

    return metadata


def parse_markdown_content(markdown_string):
    """ Parses the markdown body content into HTML """
    html = markdown.markdown(markdown_string)
    return html


def parse_post(file_contents):
    """ Parses the file contents into posts """
    metadata_string = file_contents[0:file_contents.index('%%%')].strip()
    content_string = file_contents[file_contents.index('%%%')+3:].strip()
    metadata = parse_metadata(metadata_string)
    html_content = parse_markdown_content(content_string)
    return metadata, html_content


def load_posts():
    """ Loads all the markdown files in the content folder"""
    parsed_posts = []

    for glob_filepath in glob.glob('content/*.md'):
        contents = pathlib.Path(glob_filepath).read_text()
        metadata, content = parse_post(contents)

        new_post = Post()
        setattr(new_post, 'content', content)

        for key, value in metadata.items():
            setattr(new_post, key, value)

        parsed_posts.append(new_post)

    sorted_posts = sorted(parsed_posts, key=lambda v: v.date, reverse=True)
    return sorted_posts


def group_posts_by_section(posts, config):
    """ Takes a list of posts and groups them by their section property """
    contexts = []

    # You have to sort the posts by section first for groupby to work
    sorted_posts = sorted(posts, key=lambda k: k.section)

    for section_tag, section_posts in itertools.groupby(sorted_posts, key=lambda x: x.section):
        for section in config.sections:
            if section.slug == section_tag:
                sorted_posts = sorted(list(section_posts), key=lambda p: p.date, reverse=True)
                contexts.append({
                    'slug': section.slug,
                    'posts': sorted_posts,
                    'name': section.name,
                    'order': section.order,
                    'description': section.description,
                })

    sorted_contexts = sorted(contexts, key=lambda c: c.get('order'))
    return sorted_contexts


if __name__ == '__main__':

    # Configure command-line arguments
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--flush', action='store_true', default=False)
    args = argparser.parse_args()

    # Load the config
    config = Config.load(pathlib.Path('config.json'))

    # Set up the template engine
    template_loader = jinja2.FileSystemLoader('./templates')
    template_env = jinja2.Environment(loader=template_loader)

    # Create template filters
    template_env.filters['find_section_name'] = lambda s: config.find_section_name(s)
    template_env.filters['fmt_date'] = lambda d,fmt: arrow.get(d).format(fmt)

    # Load all the templates
    content_template = template_env.get_template('content.html')
    index_template = template_env.get_template('index.html')
    section_template = template_env.get_template('section.html')

    # First, load all the posts in the content directory
    posts = load_posts()

    # Clear out any existing output
    if args.flush and pathlib.Path('output').exists():
        shutil.rmtree('output')

    # Create the expected directory structure
    pathlib.Path('output/posts').mkdir(parents=True)
    pathlib.Path('output/images').mkdir(parents=True)
    pathlib.Path('output/static').mkdir(parents=True)

    # Render all the individual posts
    for post in posts:
        content_context = {'post': post}
        content_output = content_template.render(content_context)
        pathlib.Path(f'output/posts/{post.slug}.html').write_text(content_output)

    # Copy all the post images to the output directory
    if pathlib.Path('content/images').exists():
        for glob_img_filepath in glob.glob('content/images/*'):
            src_file = pathlib.Path(glob_img_filepath)
            dst_file = pathlib.Path('output/images') / src_file.name
            shutil.copy(src_file, dst_file)

    # Render the section pages
    for section_context in group_posts_by_section(posts, config):
        slug = section_context.get('slug')
        section_output = section_template.render(section_context)
        pathlib.Path(f'output/{slug}.html').write_text(section_output)

    # Render and save the index page
    index_context = {'posts': posts}
    index_output = index_template.render(index_context)
    pathlib.Path('output/index.html').write_text(index_output)

    # Copy the static folder to the output directory
    if pathlib.Path('templates/static').exists():
        for glob_static_filepath in glob.glob('templates/static/*'):
            src_file = pathlib.Path(glob_static_filepath)
            dst_file = pathlib.Path('output/static') / src_file.name
            shutil.copy(src_file, dst_file)
