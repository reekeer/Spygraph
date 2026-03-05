import random
import string


def random_token(length=16) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def get_fingerprint() -> dict[str, str]:
    fingerprints = [
        {"Server": "Apache/2.4.41", "X-Powered-By": "PHP/7.4.3"},
        {"Server": "nginx/1.18.0", "X-Powered-By": "Express"},
        {"Server": "Microsoft-IIS/10.0", "X-Powered-By": "ASP.NET"},
        {"Server": "Apache/2.4.52", "X-Powered-By": "PHP/8.1.0"},
        {"Server": "nginx/1.20.1", "X-Powered-By": "Node.js"},
        {"Server": "LiteSpeed", "X-Powered-By": "PHP/8.0.13"},
        {"Server": "Caddy", "X-Powered-By": "Go"},
        {"Server": "Apache/2.4.48", "X-Powered-By": "Django"},
        {"Server": "nginx/1.21.0", "X-Powered-By": "Ruby on Rails"},
        {"Server": "Microsoft-IIS/8.5", "X-Powered-By": "ASP.NET Core"},
        {"Server": "Apache/2.2.15", "X-Powered-By": "PHP/5.3.3"},
        {"Server": "nginx/1.19.0", "X-Powered-By": "Flask"},
        {"Server": "Tomcat/9.0.50", "X-Powered-By": "Java"},
        {"Server": "lighttpd/1.4.59", "X-Powered-By": "PHP/7.4"},
        {"Server": "Cloudflare", "X-Powered-By": "Nginx"},
        {"Server": "Apache/2.4.54", "X-Powered-By": "Laravel"},
        {"Server": "nginx/1.22.0", "X-Powered-By": "Spring Boot"},
        {"Server": "HAProxy/2.4.0", "X-Powered-By": "Node.js/14.17"},
        {"Server": "Jetty/9.4.43", "X-Powered-By": "Java/11"},
        {"Server": "Cherokee/1.2.104", "X-Powered-By": "PHP/7.3"},
        {"Server": "nginx/1.23.0", "X-Powered-By": "Python/3.9"},
        {"Server": "Apache/2.4.51", "X-Powered-By": "WordPress"},
        {"Server": "Microsoft-IIS/7.5", "X-Powered-By": ".NET Framework 4.0"},
        {"Server": "Gunicorn/20.1.0", "X-Powered-By": "Python"},
        {"Server": "nginx/1.20.2", "X-Powered-By": "Next.js"},
    ]

    selected = random.choice(fingerprints)
    return {k: v for k, v in selected.items() if v}
