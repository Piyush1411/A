from flask import Flask, jsonify, request, flash
from flask_restful import Resource, Api
from main import app
from models import db, Section 
from routes import admin_required

api = Api(app) 
class GetSection(Resource):
    @admin_required
    def get(self):
        sections = Section.query.all()
        flash('Section data retrieved successfully.', 'info')
        return jsonify({'sections': [{
            'id': section.id,
            'name': section.name
            } for section in sections]
        })
    
api.add_resource(GetSection, '/api/section/get', methods=['GET'])
