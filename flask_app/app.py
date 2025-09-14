
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
from datetime import datetime
from research.spider import research_plant
from research.generator import generate_article
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        plant_name = request.form['plant_name']
        try:
            # Gather research
            research_data = research_plant(plant_name)
            
            # Generate article
            article = generate_article(research_data)
            
            # Prepare Jekyll post
            date = datetime.now()
            filename = f"{date.strftime('%Y-%m-%d')}-{plant_name.lower().replace(' ', '-')}.html"
            filepath = os.path.join(POSTS_DIR, filename)
            
            # Jekyll front matter
            front_matter = f"""---
title: "South African Plant Series: {plant_name}"
subtitle: "A Deep Dive into Indigenous Flora"
date: {date.strftime('%Y-%m-%d %H:%M:%S %z')}
background: '/img/posts/01.jpg'
---

"""
            # Save the post
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(front_matter + article)
            
            flash('Article generated and saved successfully!')
            return render_template('add_post.html', article=article, plant_name=plant_name, 
                                success=True)
        except Exception as e:
            flash(f'Error generating article: {str(e)}')
            return render_template('add_post.html', error=str(e))
            
    return render_template('add_post.html', article=None)

if __name__ == '__main__':
    app.run(debug=True)
