# 1. Stage EVERYTHING (this adds all files, respects .gitignore, and stages README.md)
git add .

# 2. Now commit everything that was just staged
git commit -m "Upload full project (ignoring buggy level0_data.csv)"

# 3. Push to GitHub
git push origin main