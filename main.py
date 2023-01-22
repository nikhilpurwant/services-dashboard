from flask import Flask, request, send_from_directory
from flask_cors import CORS
import traceback
from routes import (
    settings_routes,
    services_routes,
    common_routes, 
    services_only_api_routes
)
from utils import utils
from werkzeug.exceptions import HTTPException
import os
from config import Config

app = Flask(__name__)
CORS(app)

if Config.API_RUN == "N":
    app.register_blueprint(settings_routes.blueprint, url_prefix="/api")
    app.register_blueprint(services_routes.blueprint, url_prefix="/api")
    app.register_blueprint(common_routes.blueprint, url_prefix="/api")
else:
    app.register_blueprint(services_only_api_routes.blueprint, url_prefix="/api")

@app.before_request
def do_this_before_every_api_call():
    utils.add_uuid_to_g()
    utils.set_current_user_role(request)
    utils.log_with_request_id("d",f"{request.path}, {request.method}") 
    if Config.API_RUN == "Y":
        validations = utils.validate_access_to_api(request.path,request.method,False)
    else:
        validations = utils.validate_access_to_api(request.path,request.method,True)

    if not validations[0]:
        return utils.format_response(f"{request.path}, {request.method} - Access Denied","",403)
    
    validations = utils.validate_input(request.path, request.method)
    if not validations[0]:
        return utils.format_response(validations[1],"",400)            

@app.errorhandler(HTTPException)
def handle_exception(e):
    traceback.print_exc()
    utils.log_with_request_id("w",str(e.code)+"/"+e.description+e.name)
    error_code = e.code if e.code is not None else 500
    return utils.format_response(e.description,"",error_code)

@app.route('/')
def serve_static_indexpage_if_not_mentioned_in_url():
    return send_from_directory(get_base_path_for_static(), "index.html")

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(os.path.join(get_base_path_for_static()),
                               filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(get_base_path_for_static(), 'assets'),
                               filename)

def get_base_path_for_static():
    root_dir = os.path.dirname(os.getcwd())
    if os.getenv("RUNNING_IN_APP_ENGINE") == None:
        static_dir_path = os.path.join(root_dir, 'service-dashboard-api',
                                       'static')
        return static_dir_path
    else:
        return (os.path.join(root_dir, 'workspace','static'))
