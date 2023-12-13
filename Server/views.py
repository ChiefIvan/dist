from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from typing import List

from .models import User, Revoked, Credentials, Documents, Route
from .static.predef_function.user_validation import Sanitizer, RegisterEntryValidator
from .static.predef_function.image_compressor import compress_image
from . import db


views = Blueprint("views", __name__)


@views.route("/index", methods=["GET"])
@jwt_required()
def index() -> dict:
    current_user = get_jwt_identity()
    data = {}

    user: User = User.query.filter_by(id=current_user).first()
    user_credentials: Credentials = Credentials.query.filter_by(
        id=current_user).first()

    if user:
        data = {
            "email": user.email,
            "user_name": user.user_name,
            "full_ver_val": user.full_verified,
        }

    if user_credentials:
        data |= {
            "userImg": user_credentials.user_img if user_credentials else "",
            "firstName": user_credentials.firstname,
            "middleName": user_credentials.mid_init,
            "lastName": user_credentials.lastname
        }

    documents: List[Documents] = Documents.query.filter_by(
        user_id=current_user).all()
    data["documents"] = []
    for document in documents:
        document_data = {
            "documentName": document.name,
            "codeData": document.code,
            "documentDescription": document.description,
            "documentRegDate": document.doc_reg_at
        }

        routes: List[Route] = Route.query.filter_by(
            document_id=document.id).all()
        document_data["documentPath"] = [
            {"name": route.name, "approved": route.approved} for route in routes]

        data["documents"].append(document_data)

    return jsonify(data)


@views.route("/logout", methods=["GET"])
@jwt_required()
def logout() -> dict:
    jti = get_jwt()["jti"]
    now = datetime.now()
    revoked_token = Revoked(jti=jti, revoked_at=now)
    db.session.add(revoked_token)
    db.session.commit()
    return jsonify({})


@views.route("/registration", methods=["POST"])
@jwt_required()
def register():
    insertion_error: str = "Sorry, something went wrong!. Please try again."

    credentials = request.json

    current_user = get_jwt_identity()
    image = credentials["userImg"]
    first_name = credentials["firstName"]
    middle_name = credentials["middleName"]
    last_name = credentials["lastName"]

    entry_validate: RegisterEntryValidator = RegisterEntryValidator(
        image, first_name, middle_name, last_name).validate()

    if isinstance(entry_validate, dict):
        return jsonify(entry_validate)

    sanitize: bool | dict = Sanitizer(
        {"user_image": image, "first_name": first_name,
            "middle_name": middle_name, "last_name": last_name}
    ).validate()

    if isinstance(sanitize, dict):
        return jsonify(sanitize)

    user: User = User.query.filter_by(id=current_user).first()
    user_credentials: Credentials = Credentials.query.filter_by(
        user_id=current_user).first()

    image = compress_image(image, quality=80)

    if not user_credentials:
        try:
            registration: Credentials = Credentials(
                user_img=image,
                firstname=first_name,
                mid_init=middle_name,
                lastname=last_name,
                full_veri_at=datetime.now(),
                user_id=current_user,
            )

            db.session.add(registration)
            user.full_verified = True
            db.session.commit()

        except Exception as e:
            print(e)
            return jsonify({"error": insertion_error})

        return jsonify({})

    user_credentials.user_img = image
    user_credentials.firstname = first_name
    user_credentials.mid_init = middle_name
    user_credentials.lastname = last_name
    user_credentials.full_veri_at = datetime.now()
    user.full_verified = True

    db.session.commit()
    return jsonify({})


@views.route('/user_credentials_updates', methods=["GET"])
@jwt_required()
def event_polling():
    current_user = get_jwt_identity()
    user: User = User.query.filter_by(
        id=current_user).first()
    user_credentials: Credentials = Credentials.query.filter_by(
        user_id=current_user).first()
    if user_credentials:
        data = {
            "userImg": user_credentials.user_img,
            "firstName": user_credentials.firstname,
            "middleName": user_credentials.mid_init,
            "lastName": user_credentials.lastname,
            "full_ver_val": user.full_verified,
        }

        return jsonify(data)

    return jsonify({})


@views.route("/scan", methods=["POST"])
@jwt_required()
def scan():
    empty_code_data = "QR code cannot be found!"
    associated_document = "There's no document associated with the QR Code!"

    if request.method == "POST":
        scan_data = request.json

        if len(scan_data["codeData"]) == 0:
            return jsonify({"error": empty_code_data})

        document: Documents = Documents.query.filter_by(
            code=scan_data["codeData"]).first()

        if not document:
            return jsonify({"error": associated_document})

        return jsonify({"documentName": document.name, "documentDescription": document.description, "codeData": document.code, "regAt": document.doc_reg_at})

    return jsonify({})


@views.route("/document_register", methods=["POST"])
@jwt_required()
def document_register():
    insertion_error: str = "Sorry, something went wrong!. Please try again."

    if request.method == "POST":
        data = request.json

        print(data)

        entry_validate: RegisterEntryValidator = RegisterEntryValidator(
            data["codeData"], data["documentName"], data["documentDescription"]).validate()

        if isinstance(entry_validate, dict):
            return jsonify(entry_validate)

        sanitize: bool | dict = Sanitizer(
            {"Document Name": data["documentName"], "Document Code": data["codeData"],
                "Document Descripttion": data["documentDescription"]}
        ).validate()

        if isinstance(sanitize, dict):
            return jsonify(sanitize)

        document: Documents = Documents.query.filter_by(
            name=data["documentName"]).first()

        if not document:
            return jsonify({"error": "Your Route Name must be equal to Document Name"})

        document.doc_reg_at = datetime.now()
        document.code = data["codeData"]
        document.description = data["documentDescription"]

        db.session.commit()

        return jsonify({
            "documentName": document.name,
            "codeData": document.code,
            "documentDescription": document.description,
            "documentRegDate": document.doc_reg_at
        })

    return jsonify({})


@views.route("/add_route", methods=["POST"])
@jwt_required()
def add_route():
    if request.method == "POST":
        route = request.json
        name = route["routeName"]
        current_user = get_jwt_identity()

        document = Documents.query.filter_by(name=name).first()

        if document:
            return jsonify({"error": "There's already a Route for this Document!"})

        new_document = Documents(name=name, user_id=current_user)
        db.session.add(new_document)
        db.session.commit()

        for name in route["documentPath"].values():
            new_route = Route(name=name,
                              document_id=new_document.id)
            db.session.add(new_route)

        db.session.commit()
    return jsonify({})


from flask import jsonify

@views.route("/get_all", methods=["GET"])
def get_all():
    routes = Route.query.all()
    
    all_data = {
        "users": [],
        "routes": list(set([route.name for route in routes]))
    }

    all_users = User.query.all()
    for user in all_users:
        user_credential = Credentials.query.filter_by(user_id=user.id).first()
        user_documents = Documents.query.filter_by(user_id=user.id).all()
        
        user_data = {
            "firstName": user_credential.firstname if user_credential else "",
            "middleName": user_credential.mid_init if user_credential else "",
            "lastName": user_credential.lastname if user_credential else "",
            "userImg": user_credential.user_img if user_credential else "",
            "documents": []
        }

        for document in user_documents:
            document_data = {
                "documentID": document.id,
                "codeData": document.code,
                "documentName": document.name,
                "documentDescription": document.description,
                "documentRegDate": document.doc_reg_at,
                "documentPath": []
            }
            
            all_document_routes = Route.query.filter_by(document_id=document.id).all()
            for route in all_document_routes:
                document_data["documentPath"].append({
                    "name": route.name,
                    "approved": route.approved
                })
            
            user_data["documents"].append(document_data)

        all_data["users"].append(user_data)
    
    return jsonify(all_data)

