from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

import logging
logger = logging.getLogger(__name__)

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email', username)
        logger.debug(f"Tentative de connexion avec email: {email}")
        
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password):
                logger.debug("Connexion réussie")
                return user
            logger.warning("Mot de passe incorrect")
        except UserModel.DoesNotExist:
            logger.warning(f"Email {email} non trouvé")
        
        return None