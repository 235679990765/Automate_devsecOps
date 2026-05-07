LANGUAGE_PROFILES = {

    "python": {
        "setup": """
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
""",

        "install": """
      - name: Install Dependencies
        run: |
          pip install -r requirements.txt || true
"""
    },

    "node": {
        "setup": """
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
""",

        "install": """
      - name: Install Dependencies
        run: npm install
"""
    },

    "java": {
        "setup": """
      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '21'
""",

        "install": ""
    },

    "go": {
        "setup": """
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'
""",

        "install": """
      - name: Download Dependencies
        run: go mod download
"""
    },

    "rust": {
        "setup": """
      - name: Setup Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
""",

        "install": ""
    },

    "php": {
        "setup": """
      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
""",

        "install": """
      - name: Install Composer Dependencies
        run: composer install
"""
    },

    "dotnet": {
        "setup": """
      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
""",

        "install": """
      - name: Restore Dependencies
        run: dotnet restore
"""
    },

    "frontend-static": {
        "setup": "",
        "install": ""
    }
}